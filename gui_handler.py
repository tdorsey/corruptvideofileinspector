"""
GUI functionality for Corrupt Video Inspector
Handles all tkinter-based user interface components and GUI-specific logic.
"""
import os
import subprocess
import shlex
import signal
import time
import psutil
from threading import Thread
from datetime import datetime
from utils import (is_macos, is_windows_os, is_linux_os, truncate_filename, 
                   convert_time, calculate_progress, get_all_video_files, count_all_video_files)
from video_inspector import VideoObject, get_all_video_object_files

# Try to import tkinter - fail gracefully if not available
try:
    import tkinter as tk
    from tkinter import filedialog
    from tkinter import ttk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None

# Try to import tkmacosx only on macOS
try:
    if is_macos():
        from tkmacosx import Button as MacButton
    else:
        MacButton = None
except ImportError:
    MacButton = None


# Global variables for process management
g_progress = None
g_count = None
g_currently_processing = None
g_mac_pid = ''
g_windows_pid = ''


def select_directory(root, label_select_directory, button_select_directory):
    """Handle directory selection from file dialog"""
    directory = filedialog.askdirectory()

    if len(directory) > 0:
        label_select_directory.destroy()
        button_select_directory.destroy()
        after_directory_chosen(root, directory)


def windows_ffmpeg_cpu_calculation_primer():
    """Prime CPU calculation for Windows ffmpeg monitoring"""
    # https://psutil.readthedocs.io/en/latest/#psutil.cpu_percent
    # https://stackoverflow.com/questions/24367424/cpu-percentinterval-none-always-returns-0-regardless-of-interval-value-python
    process_names = [proc for proc in psutil.process_iter()]
    for proc in process_names:
        if "ffmpeg" in proc.name():
            cpu_usage = proc.cpu_percent()


def verify_ffmpeg_still_running(root):
    """Display ffmpeg status in a popup window"""
    ffmpeg_window = tk.Toplevel(root)
    ffmpeg_window.resizable(False, False)
    ffmpeg_window.geometry("400x150")
    ffmpeg_window.title("Verify ffmpeg Status")
    output = ''
    cpu_usage = ''

    if is_macos():
        proc = subprocess.Popen("ps -Ao comm,pcpu -r | head -n 10 | grep ffmpeg", shell=True, stdout=subprocess.PIPE)
        output = proc.communicate()[0].decode('utf-8').strip()
        if "ffmpeg" in output:
            cpu_usage = output.split()[1]
            output = f"ffmpeg is currently running.\nffmpeg is currently using {cpu_usage}% of CPU"
        else:
            output = "ffmpeg is NOT currently running!"
    if is_windows_os():
        windows_ffmpeg_cpu_calculation_primer()
        found = False
        process_names = [proc for proc in psutil.process_iter()]
        for proc in process_names:
            if "ffmpeg" in proc.name():
                cpu_usage = proc.cpu_percent()
                found = True
                break
        if found:
            output = f"ffmpeg is currently running.\nffmpeg is currently using {cpu_usage}% of CPU"
        else:
            output = "ffmpeg is NOT currently running!"

    label_ffmpeg_result = tk.Label(ffmpeg_window, width=375, text=output, font=('Helvetica', 14))
    label_ffmpeg_result.pack(fill=tk.X, pady=20)


def kill_ffmpeg_warning(root, log_file):
    """Show warning dialog before killing ffmpeg process"""
    ffmpeg_kill_window = tk.Toplevel(root)
    ffmpeg_kill_window.resizable(False, False)
    if is_macos():
        ffmpeg_kill_window.geometry("400x300")
    elif is_windows_os():
        ffmpeg_kill_window.geometry("400x400")
    ffmpeg_kill_window.title("Safely Quit Program")

    label_ffmpeg_kill = tk.Label(ffmpeg_kill_window, wraplength=375, width=375, text="This application spawns a subprocess named 'ffmpeg'. If this program is quit using the 'X' button, for example, the 'ffmpeg' subprocess will continue to run in the background of the host computer, draining the CPU resources. Clicking the button below will terminate the 'ffmpeg' subprocess and safely quit the application. This will prematurely end all video processing. Only do this if you want to safely exit the program and clean all subprocesses", font=('Helvetica', 14))
    label_ffmpeg_kill.pack(fill=tk.X, pady=20)

    if is_macos() and MacButton:
        # https://stackoverflow.com/questions/1529847/how-to-change-the-foreground-or-background-colour-of-a-tkinter-button-on-mac-os
        button_kill_ffmpeg = MacButton(ffmpeg_kill_window, background='#E34234', borderless=1, foreground='white', text="Terminate Program", width=500, command=lambda: kill_ffmpeg(root, log_file))
        button_kill_ffmpeg.pack(pady=10)
    else:
        button_kill_ffmpeg = tk.Button(ffmpeg_kill_window, background='#E34234', foreground='white', text="Terminate Program", width=200, command=lambda: kill_ffmpeg(root, log_file))
        button_kill_ffmpeg.pack(pady=10)


def kill_ffmpeg(root, log_file):
    """Kill ffmpeg process and exit application"""
    if is_macos():
        try:
            global g_mac_pid
            log_file.write(f'---USER MANUALLY TERMINATED PROGRAM---\n')
            os.killpg(os.getpgid(g_mac_pid), signal.SIGTERM)
        except Exception as e:
            log_file.write(f'ERROR in "kill_ffmpeg": {e}\n')
            log_file.flush()
    elif is_windows_os():
        try:
            global g_windows_pid
            log_file.write(f'---USER MANUALLY TERMINATED PROGRAM---\n')
            for proc in psutil.process_iter():
                if proc.name() == "ffmpeg.exe" or proc.name() == "CorruptVideoInspector.exe":
                    proc.kill()
            log_file.flush()
        except Exception as e:
            log_file.write(f'ERROR in "kill_ffmpeg": {e}\n')
            log_file.flush()


def inspect_video_files_gui(directory, tkinter_window, listbox_completed_videos, index_start, log_file, progress_bar):
    """GUI version of video file inspection - main processing thread"""
    try:
        global g_count
        global g_currently_processing

        log_file.write('CREATED: _Logs.log\n')
        log_file.write('CREATED: _Results.csv\n')
        log_file.write('=================================================================\n')
        log_file.flush()

        # CSV Results file
        results_file_path = os.path.join(directory, '_Results.csv')
        results_file_exists = os.path.isfile(results_file_path)
        if results_file_exists:
            os.remove(results_file_path)

        import csv
        results_file = open(results_file_path, 'a+', encoding="utf8", newline='')
        results_file_writer = csv.writer(results_file)

        header = ['Video File', 'Corrupted']
        results_file_writer.writerow(header)
        results_file.flush()

        totalVideoFiles = count_all_video_files(directory)
        start_time = datetime.now().strftime('%Y-%m-%d %I:%M %p')

        log_file.write(f'DIRECTORY: {directory}\n')
        log_file.write(f'TOTAL VIDEO FILES FOUND: {totalVideoFiles}\n')
        log_file.write(f'STARTING FROM VIDEO INDEX: {index_start}\n')
        log_file.write(f'START TIME: {start_time}\n')
        log_file.write('=================================================================\n')
        log_file.write('(DURATION IS IN HOURS:MINUTES:SECONDS)\n')
        log_file.flush()

        all_videos_found = get_all_video_object_files(directory)

        count = 0
        for video in all_videos_found:
            if (index_start > count + 1):
                count += 1
                continue

            start_time = time.time()

            global g_progress
            g_progress.set(calculate_progress(count, totalVideoFiles))
            tkinter_window.update()

            g_count.set(f"{count + 1} / {totalVideoFiles}")
            tkinter_window.update()

            g_currently_processing.set(truncate_filename(video.filename))
            tkinter_window.update()

            proc = ''
            if is_macos():
                global g_mac_pid
                proc = subprocess.Popen(f'./ffmpeg -v error -i {shlex.quote(video.full_filepath)} -f null - 2>&1', shell=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                g_mac_pid = proc.pid
            elif is_windows_os():
                global g_windows_pid
                ffmpeg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ffmpeg.exe'))
                proc = subprocess.Popen(f'"{ffmpeg_path}" -v error -i "{video.full_filepath}" -f null error.log', shell=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                g_windows_pid = proc.pid
            else:
                # Linux - use system ffmpeg or bundled ffmpeg if available
                ffmpeg_cmd = 'ffmpeg'  # Try system ffmpeg first
                # Check if bundled ffmpeg exists and works
                ffmpeg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ffmpeg'))
                if os.path.isfile(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
                    try:
                        subprocess.run([ffmpeg_path, '-version'], capture_output=True, check=True, timeout=5)
                        ffmpeg_cmd = ffmpeg_path
                    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired, OSError):
                        pass  # Fall back to system ffmpeg
                proc = subprocess.Popen(f'{ffmpeg_cmd} -v error -i {shlex.quote(video.full_filepath)} -f null - 2>&1', 
                                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            output, error = proc.communicate()

            # Debug
            logging.debug(f'output= {output}')
            logging.debug(f'error= {error}')

            row_index = count
            if (index_start != 1):
                row_index = (count + 1) - index_start

            # Determine if video is corrupt
            ffmpeg_result = ''
            if is_macos() or is_linux_os():
                ffmpeg_result = output
            elif is_windows_os():
                ffmpeg_result = error

            elapsed_time = time.time() - start_time
            readable_time = convert_time(elapsed_time)
            row = ''
            if not ffmpeg_result:
                # Healthy
                print("\033[92m{0}\033[00m".format("HEALTHY -> {}".format(video.filename)), end='\n')  # green

                log_file.write('=================================================================\n')
                log_file.write(f'{video.filename}\n')
                log_file.write('STATUS: ✓ HEALTHY ✓\n')
                log_file.write(f'DURATION: {readable_time}\n')
                log_file.flush()

                row = [video.filename, 0]
                listbox_completed_videos.insert(tk.END, f' {video.filename}')
                listbox_completed_videos.itemconfig(row_index, bg='green')
                tkinter_window.update()
            else:
                # Corrupt
                print("\033[31m{0}\033[00m".format("CORRUPTED -> {}".format(video.filename)), end='\n')  # red

                log_file.write('=================================================================\n')
                log_file.write(f'{video.filename}\n')
                log_file.write('STATUS: X CORRUPT X\n')
                log_file.write(f'DURATION: {readable_time}\n')
                log_file.flush()

                row = [video.filename, 1]
                listbox_completed_videos.insert(tk.END, f' {video.filename}')
                listbox_completed_videos.itemconfig(row_index, bg='red')
                tkinter_window.update()

            results_file_writer.writerow(row)
            results_file.flush()

            count += 1

            g_progress.set(calculate_progress(count, totalVideoFiles))
            tkinter_window.update()

        g_count.set("---")
        g_currently_processing.set("N/A")
        progress_bar.stop()
        progress_bar['value'] = 100
        tkinter_window.update()

        results_file.flush()
        results_file.close()

        end_time = datetime.now().strftime('%Y-%m-%d %I:%M %p')

        print(f'Finished: {end_time}')
        log_file.write('=================================================================\n')
        log_file.write(f'SUCCESSFULLY PROCESSED {(totalVideoFiles + 1) - index_start} VIDEO FILES\n')
        log_file.write(f'END TIME: {end_time}\n')
        log_file.write('=================================================================\n')
        log_file.flush()
        log_file.close()
    except Exception as e:
        log_file.write(f'ERROR in "inspect_video_files_gui" (aka main thread): {e}\n')
        log_file.flush()


def start_program(directory, root, index_start, log_file, label_chosen_directory, label_chosen_directory_var, label_video_count, label_video_count_var, label_index_start, entry_index_input, label_explanation, button_start, listbox_completed_videos):
    """Start the video inspection process from GUI"""
    try:
        # Clean up directory selection UI
        label_chosen_directory.destroy()
        label_chosen_directory_var.destroy()
        label_video_count.destroy()
        label_video_count_var.destroy()
        label_index_start.destroy()
        entry_index_input.destroy()
        label_explanation.destroy()
        button_start.destroy()
        listbox_completed_videos.destroy()

        # Create progress UI
        label_progress_text = tk.Label(root, text="Progress:", font=('Helvetica Bold', 18))
        label_progress_text.pack(fill=tk.X, pady=10)

        g_progress.set("0%")
        label_progress_var = tk.Label(root, textvariable=g_progress, font=('Helvetica', 50))
        label_progress_var.pack(fill=tk.X, pady=(0, 10))

        progress_bar = ttk.Progressbar(root, orient="horizontal", mode="indeterminate", length=300)
        progress_bar.pack(pady=(0, 20))
        progress_bar.start()

        label_currently_processing_text = tk.Label(root, text="Currently Processing:", font=('Helvetica Bold', 18))
        label_currently_processing_text.pack(fill=tk.X, pady=10)

        g_count.set("0 / 0")
        label_count_var = tk.Label(root, textvariable=g_count, font=('Helvetica', 16))
        label_count_var.pack(fill=tk.X, pady=(0, 10))

        g_currently_processing.set("N/A")
        label_currently_processing_var = tk.Label(root, textvariable=g_currently_processing, font=('Helvetica', 16))
        label_currently_processing_var.pack(fill=tk.X, pady=(0, 10))

        listbox_completed_videos = tk.Listbox(root, font=('Helvetica', 16))
        listbox_completed_videos.pack(expand=False, fill=tk.BOTH, side=tk.TOP, padx=10, pady=10)
        listbox_completed_videos.bind('<<ListboxSelect>>', lambda e: "break")
        listbox_completed_videos.bind('<Button-1>', lambda e: "break")
        listbox_completed_videos.bind('<Button-2>', lambda e: "break")
        listbox_completed_videos.bind('<Button-3>', lambda e: "break")
        listbox_completed_videos.bind('<ButtonRelease-1>', lambda e: "break")
        listbox_completed_videos.bind('<Double-1>', lambda e: "break")
        listbox_completed_videos.bind('<Double-Button-1>', lambda e: "break")
        listbox_completed_videos.bind('<B1-Motion>', lambda e: "break")

        button_ffmpeg_verify = tk.Button(root, text="ffmpeg Status", width=200, command=lambda: verify_ffmpeg_still_running(root))
        button_ffmpeg_verify.pack(pady=10)

        if is_macos() and MacButton:
            # https://stackoverflow.com/questions/1529847/how-to-change-the-foreground-or-background-colour-of-a-tkinter-button-on-mac-os
            button_kill_ffmpeg = MacButton(root, background='#E34234', borderless=1, foreground='white', text="Safely Quit", width=500, command=lambda: kill_ffmpeg_warning(root, log_file))
            button_kill_ffmpeg.pack(pady=10)
        else:
            button_kill_ffmpeg = tk.Button(root, background='#E34234', foreground='white', text="Safely Quit", width=200, command=lambda: kill_ffmpeg_warning(root, log_file))
            button_kill_ffmpeg.pack(pady=10)

        thread = Thread(target=inspect_video_files_gui, args=(directory, root, listbox_completed_videos, index_start, log_file, progress_bar))
        thread.start()
    except Exception as e:
        log_file.write(f'ERROR in "start_program": {e}\n')
        log_file.flush()


def after_directory_chosen(root, directory):
    """Handle directory selection and setup the main GUI"""
    # Log file
    log_file_path = os.path.join(directory, '_Logs.log')
    log_file_exists = os.path.isfile(log_file_path)
    if log_file_exists:
        os.remove(log_file_path)
    log_file = open(log_file_path, 'a', encoding="utf8")

    # Logging
    print('CORRUPT VIDEO FILE INSPECTOR')
    print('')
    log_file.write('=================================================================\n')
    log_file.write('                CORRUPT VIDEO FILE INSPECTOR\n')
    log_file.write('=================================================================\n')
    log_file.flush()

    totalVideos = count_all_video_files(directory)

    label_chosen_directory = tk.Label(root, text="Chosen directory:", font=('Helvetica Bold', 18))
    label_chosen_directory.pack(fill=tk.X, pady=5)
    label_chosen_directory_var = tk.Label(root, wraplength=450, text=f"{directory}", font=('Helvetica', 14))
    label_chosen_directory_var.pack(fill=tk.X, pady=(5, 20))

    label_video_count = tk.Label(root, text="Total number of videos found:", font=('Helvetica Bold', 18))
    label_video_count.pack(fill=tk.X, pady=5)
    label_video_count_var = tk.Label(root, text=f"{totalVideos}", font=('Helvetica', 16))
    label_video_count_var.pack(fill=tk.X, pady=(5, 20))

    listbox_videos_found_with_index = tk.Listbox(root, font=('Helvetica', 16), width=480)
    listbox_videos_found_with_index.pack(padx=10)
    listbox_videos_found_with_index.bind('<<ListboxSelect>>', lambda e: "break")
    listbox_videos_found_with_index.bind('<Button-1>', lambda e: "break")
    listbox_videos_found_with_index.bind('<Button-2>', lambda e: "break")
    listbox_videos_found_with_index.bind('<Button-3>', lambda e: "break")
    listbox_videos_found_with_index.bind('<ButtonRelease-1>', lambda e: "break")
    listbox_videos_found_with_index.bind('<Double-1>', lambda e: "break")
    listbox_videos_found_with_index.bind('<Double-Button-1>', lambda e: "break")
    listbox_videos_found_with_index.bind('<B1-Motion>', lambda e: "break")

    all_videos_found = get_all_video_files(directory)
    for video in all_videos_found:
        listbox_videos_found_with_index.insert(tk.END, video)
    root.update()

    label_index_start = tk.Label(root,
                                 text=f"Start at video index (1 - {count_all_video_files(directory)}):",
                                 font=('Helvetica Bold', 18))
    label_index_start.pack(fill=tk.X, pady=5)

    entry_index_input = tk.Entry(root, width=50)
    entry_index_input.focus_set()
    entry_index_input.insert(tk.END, '1')
    entry_index_input.pack(fill=tk.X, padx=200)

    label_explanation = tk.Label(root, wraplength=450,
                                 text="The default is '1'. Set index to '1' if you want to start from the beginning and process all videos. If you are resuming a previous operation, then set the index to the desired number. Also note, each run will overwrite the _Logs and _Results files.",
                                 font=('Helvetica Italic', 12))
    label_explanation.pack(fill=tk.X, pady=5, padx=20)

    if totalVideos > 0:
        button_start = tk.Button(root, text="Start Inspecting", width=25, command=lambda: start_program(directory, root, int(entry_index_input.get()), log_file, label_chosen_directory, label_chosen_directory_var, label_video_count, label_video_count_var, label_index_start, entry_index_input, label_explanation, button_start, listbox_videos_found_with_index))
        button_start.pack(pady=20)
    else:
        root.withdraw()
        error_window = tk.Toplevel(root)
        error_window.resizable(False, False)
        error_window.geometry("400x200")
        error_window.title("Error")

        label_error_msg = tk.Label(error_window, width=375, text="No video files found in selected directory!", font=('Helvetica', 14))
        label_error_msg.pack(fill=tk.X, pady=20)

        button_exit = tk.Button(error_window, text="Exit", width=30, command=lambda: sys.exit())
        button_exit.pack()


def run_gui_mode():
    """Initialize and run the GUI interface"""
    if not TKINTER_AVAILABLE:
        print("Error: tkinter is not available. GUI mode requires tkinter.")
        print("Please install tkinter or use CLI mode by providing a directory argument.")
        print("Example: python CorruptVideoInspector.py /path/to/videos")
        return False

    global g_progress, g_count, g_currently_processing, g_mac_pid, g_windows_pid

    root = tk.Tk()
    root.title("Corrupt Video Inspector")
    if is_macos():
        root.geometry("500x650")
    if is_windows_os():
        root.geometry("500x750")
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'icon.ico'))
        if os.path.exists(icon_path):
            root.iconbitmap(default=icon_path)
    if is_linux_os():
        root.geometry("500x750")
    
    g_progress = tk.StringVar()
    g_count = tk.StringVar()
    g_currently_processing = tk.StringVar()
    g_mac_pid = ''
    g_windows_pid = ''

    label_select_directory = tk.Label(root, wraplength=450, justify="left", text="Select a directory to search for all video files within the chosen directory and all of its containing subdirectories", font=('Helvetica', 16))
    label_select_directory.pack(fill=tk.X, pady=20, padx=20)

    button_select_directory = tk.Button(root, text="Select Directory", width=20, command=lambda: select_directory(root, label_select_directory, button_select_directory))
    button_select_directory.pack(pady=20)

    root.mainloop()
    return True
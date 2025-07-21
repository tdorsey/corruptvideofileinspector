import argparse
import csv
import json
import os
import subprocess
import shlex
import platform
import psutil
import signal
import sys
import time
from threading import Thread
from datetime import datetime

# Try to import tkinter for GUI mode - fail gracefully if not available
try:
    import tkinter as tk
    from tkinter import filedialog
    from tkinter import ttk
    from tkmacosx import Button as MacButton
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    # Create dummy objects for when tkinter is not available
    tk = None

VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', '.webm', '.m4v', '.m4p', '.mpeg', '.mpg', '.3gp', '.3g2']

# ========================== CLASSES ===========================

class VideoObject():
    def __init__(self, filename, full_filepath):
        self.filename = filename
        self.full_filepath = full_filepath

# ========================= FUNCTIONS ==========================

def isMacOs():
    if 'Darwin' in platform.system():
        return True
    return False

def isWindowsOs():
    if 'Windows' in platform.system():
        return True
    return False

def isLinuxOs():
    if 'Linux' in platform.system():
        return True
    return False

def selectDirectory(root, label_select_directory, button_select_directory):
    # root.withdraw()
    directory = filedialog.askdirectory()

    if len(directory) > 0:
        label_select_directory.destroy()
        button_select_directory.destroy()
        afterDirectoryChosen(root, directory)


def convertTime(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)

def truncateFilename(input):
    file_name, file_extension = os.path.splitext(input)
    if isMacOs() and len(file_name) > 50:
        truncated_string = file_name[0:49]
        return f'{truncated_string}..{file_extension}'
    elif isWindowsOs() and len(file_name) > 42:
        truncated_string = file_name[0:41]
        return f'{truncated_string}..{file_extension}'
    else:
        return input

def countAllVideoFiles(dir):
    total = 0
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.lower().endswith(tuple(VIDEO_EXTENSIONS)):
                total += 1
    return total

def getAllVideoFiles(dir):
    videos_found_list = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.lower().endswith(tuple(VIDEO_EXTENSIONS)):
                videos_found_list.append(file)
    videos_found_list.sort()
    index = 1
    sorted_videos_list = []
    for video in videos_found_list:
        sorted_videos_list.append(f' {index}:  {video}')
        index += 1
    return sorted_videos_list

def getAllVideoObjectFiles(dir):
    """Get all video files as VideoObject instances for CLI processing"""
    videos_found_list = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if file.lower().endswith(tuple(VIDEO_EXTENSIONS)):
                full_path = os.path.join(root, file)
                videos_found_list.append(VideoObject(file, full_path))
    
    # Sort by filename
    videos_found_list.sort(key=lambda x: x.filename.lower())
    return videos_found_list

def windowsFfmpegCpuCalculationPrimer():
    # https://psutil.readthedocs.io/en/latest/#psutil.cpu_percent
    # https://stackoverflow.com/questions/24367424/cpu-percentinterval-none-always-returns-0-regardless-of-interval-value-python
    process_names = [proc for proc in psutil.process_iter()]
    for proc in process_names:
        if "ffmpeg" in proc.name():
            cpu_usage = proc.cpu_percent()

def verify_ffmpeg_still_running(root):
    ffmpeg_window = tk.Toplevel(root)
    ffmpeg_window.resizable(False, False)
    ffmpeg_window.geometry("400x150")
    ffmpeg_window.title("Verify ffmpeg Status")
    output = ''
    cpu_usage = ''

    if isMacOs():
        proc = subprocess.Popen("ps -Ao comm,pcpu -r | head -n 10 | grep ffmpeg", shell=True, stdout=subprocess.PIPE)
        output = proc.communicate()[0].decode('utf-8').strip()
        if "ffmpeg" in output:
            cpu_usage = output.split()[1]
            output = f"ffmpeg is currently running.\nffmpeg is currently using {cpu_usage}% of CPU"
        else:
            output = "ffmpeg is NOT currently running!"
    if isWindowsOs():
        windowsFfmpegCpuCalculationPrimer()
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
    ffmpeg_kill_window = tk.Toplevel(root)
    ffmpeg_kill_window.resizable(False, False)
    if isMacOs():
        ffmpeg_kill_window.geometry("400x300")
    elif isWindowsOs():
        ffmpeg_kill_window.geometry("400x400")
    ffmpeg_kill_window.title("Safely Quit Program")

    label_ffmpeg_kill = tk.Label(ffmpeg_kill_window, wraplength=375, width=375, text="This application spawns a subprocess named 'ffmpeg'. If this program is quit using the 'X' button, for example, the 'ffmpeg' subprocess will continue to run in the background of the host computer, draining the CPU resources. Clicking the button below will terminate the 'ffmpeg' subprocess and safely quit the application. This will prematurely end all video processing. Only do this if you want to safely exit the program and clean all subprocesses", font=('Helvetica', 14))
    label_ffmpeg_kill.pack(fill=tk.X, pady=20)

    if isMacOs():
        # https://stackoverflow.com/questions/1529847/how-to-change-the-foreground-or-background-colour-of-a-tkinter-button-on-mac-os
        button_kill_ffmpeg = MacButton(ffmpeg_kill_window, background='#E34234', borderless=1, foreground='white', text="Terminate Program", width=500, command=lambda: kill_ffmpeg(root, log_file))
        button_kill_ffmpeg.pack(pady=10)
    elif isWindowsOs():
        button_kill_ffmpeg = tk.Button(ffmpeg_kill_window, background='#E34234', foreground='white', text="Terminate Program", width=200, command=lambda: kill_ffmpeg(root, log_file))
        button_kill_ffmpeg.pack(pady=10)

def kill_ffmpeg(root, log_file):
    if isMacOs():
        try:
            global g_mac_pid
            log_file.write(f'---USER MANUALLY TERMINATED PROGRAM---\n')
            os.killpg(os.getpgid(g_mac_pid), signal.SIGTERM)
        except Exception as e:
            log_file.write(f'ERROR in "kill_ffmpeg": {e}\n')
            log_file.flush()
    elif isWindowsOs():
        try:
            global g_windows_pid
            # os.kill(g_windows_pid, signal.CTRL_C_EVENT)
            # subprocess.Popen("taskkill /F /T /PID %i" % g_windows_pid, shell=True)
            log_file.write(f'---USER MANUALLY TERMINATED PROGRAM---\n')
            for proc in psutil.process_iter():
                if proc.name() == "ffmpeg.exe" or proc.name() == "CorruptVideoInspector.exe":
                    proc.kill()
            log_file.flush()
        except Exception as e:
            log_file.write(f'ERROR in "kill_ffmpeg": {e}\n')
            log_file.flush()


def estimatedTime(total_videos):
    # estimating 3 mins per 2GB video file, on average
    total_minutes = total_videos * 3
    # Get hours with floor division
    hours = total_minutes // 60
    # Get additional minutes with modulus
    minutes = total_minutes % 60
    # Create time as a string
    time_string = "{} hours, {} minutes".format(hours, minutes)
    return time_string


def calculateProgress(count, total):
    return "{0}%".format(int((count / total) * 100))

def inspectVideoFiles(directory, tkinter_window, listbox_completed_videos, index_start, log_file, progress_bar):
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

        results_file = open(results_file_path, 'a+', encoding="utf8", newline='')
        results_file_writer = csv.writer(results_file)

        header = ['Video File', 'Corrupted']
        results_file_writer.writerow(header)
        results_file.flush()

        totalVideoFiles = countAllVideoFiles(directory)
        start_time = datetime.now().strftime('%Y-%m-%d %I:%M %p')

        log_file.write(f'DIRECTORY: {directory}\n')
        log_file.write(f'TOTAL VIDEO FILES FOUND: {totalVideoFiles}\n')
        log_file.write(f'STARTING FROM VIDEO INDEX: {index_start}\n')
        log_file.write(f'START TIME: {start_time}\n')
        log_file.write('=================================================================\n')
        log_file.write('(DURATION IS IN HOURS:MINUTES:SECONDS)\n')
        log_file.flush()

        all_videos_found = []
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith(tuple(VIDEO_EXTENSIONS)):
                    video_obj = VideoObject(filename, os.path.join(root, filename))
                    all_videos_found.append(video_obj)

        # Alphabetize list
        all_videos_found.sort(key=lambda x: x.filename)

        count = 0
        for video in all_videos_found:
            if (index_start > count + 1):
                count += 1
                continue

            start_time = time.time()

            global g_progress
            g_progress.set(calculateProgress(count, totalVideoFiles))
            tkinter_window.update()

            g_count.set(f"{count + 1} / {totalVideoFiles}")
            tkinter_window.update()

            g_currently_processing.set(truncateFilename(video.filename))
            tkinter_window.update()

            proc = ''
            if isMacOs():
                global g_mac_pid
                proc = subprocess.Popen(f'./ffmpeg -v error -i {shlex.quote(video.full_filepath)} -f null - 2>&1', shell=True,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                g_mac_pid = proc.pid
            elif isWindowsOs():
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
            print(f'output= {output}\n')
            print(f'error= {error}\n')

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
            readable_time = convertTime(elapsed_time)
            row = ''
            if not ffmpeg_result:
                # Healthy
                print("\033[92m{0}\033[00m".format("HEALTHY -> {}".format(video.filename)), end='\n')  # red

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

            g_progress.set(calculateProgress(count, totalVideoFiles))
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
        log_file.write(f'ERROR in "inspectVideoFiles" (aka main thread): {e}\n')
        log_file.flush()

def start_program(directory, root, index_start, log_file, label_chosen_directory, label_chosen_directory_var, label_video_count, label_video_count_var, label_index_start, entry_index_input, label_explanation, button_start, listbox_completed_videos):
    try:
        label_chosen_directory.destroy()
        label_chosen_directory_var.destroy()
        label_video_count.destroy()
        label_video_count_var.destroy()
        label_index_start.destroy()
        entry_index_input.destroy()
        label_explanation.destroy()
        button_start.destroy()
        listbox_completed_videos.destroy()

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

        if isMacOs():
            # https://stackoverflow.com/questions/1529847/how-to-change-the-foreground-or-background-colour-of-a-tkinter-button-on-mac-os
            button_kill_ffmpeg = MacButton(root, background='#E34234', borderless=1, foreground='white', text="Safely Quit", width=500, command=lambda: kill_ffmpeg_warning(root, log_file))
            button_kill_ffmpeg.pack(pady=10)
        elif isWindowsOs():
            button_kill_ffmpeg = tk.Button(root, background='#E34234', foreground='white', text="Safely Quit", width=200, command=lambda: kill_ffmpeg_warning(root, log_file))
            button_kill_ffmpeg.pack(pady=10)

        thread = Thread(target=inspectVideoFiles, args=(directory, root, listbox_completed_videos, index_start, log_file, progress_bar))
        thread.start()
    except Exception as e:
        log_file.write(f'ERROR in "start_program": {e}\n')
        log_file.flush()

def afterDirectoryChosen(root, directory):
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

    totalVideos = countAllVideoFiles(directory)

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

    all_videos_found = getAllVideoFiles(directory)
    for video in all_videos_found:
        listbox_videos_found_with_index.insert(tk.END, video)
    root.update()

    label_index_start = tk.Label(root,
                                 text=f"Start at video index (1 - {countAllVideoFiles(directory)}):",
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

        button_exit = tk.Button(error_window, text="Exit", width=30, command=lambda: exit())
        button_exit.pack()

# ========================= CLI FUNCTIONS ==========================

def get_state_file_path(directory):
    """Get the path for the state file for a given directory"""
    safe_dir_name = os.path.basename(directory.rstrip('/\\'))
    if not safe_dir_name:
        safe_dir_name = "root"
    # Replace problematic characters
    safe_dir_name = "".join(c for c in safe_dir_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return os.path.join(directory, f".corruptvideo_scan_state_{safe_dir_name}.json")

def save_scan_state(directory, video_files, processed_files, scan_metadata):
    """Save the current scan state to a JSON file"""
    state_file = get_state_file_path(directory)
    state_data = {
        'directory': directory,
        'scan_metadata': scan_metadata,
        'total_files': len(video_files),
        'video_files': [{'filename': v.filename, 'full_filepath': v.full_filepath} for v in video_files],
        'processed_files': processed_files,
        'last_updated': datetime.now().isoformat()
    }
    
    try:
        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save state file: {e}")

def load_scan_state(directory):
    """Load the scan state from a JSON file if it exists"""
    state_file = get_state_file_path(directory)
    if not os.path.exists(state_file):
        return None
    
    try:
        with open(state_file, 'r') as f:
            state_data = json.load(f)
        
        # Validate the state file
        if state_data.get('directory') != directory:
            return None
            
        return state_data
    except Exception as e:
        print(f"Warning: Could not load state file: {e}")
        return None

def get_ffmpeg_command():
    """Get the appropriate ffmpeg command for the current platform"""
    # First check if system ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return 'ffmpeg'
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Check for bundled ffmpeg
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if isWindowsOs():
        bundled_path = os.path.join(script_dir, 'ffmpeg.exe')
    else:
        bundled_path = os.path.join(script_dir, 'ffmpeg')
    
    if os.path.exists(bundled_path) and os.access(bundled_path, os.X_OK):
        return bundled_path
    
    return None

def inspect_video_files_cli(directory, resume=True, verbose=False, json_output=False):
    """CLI version of video file inspection with automatic resume functionality"""
    
    # Get all video files in directory
    video_files = getAllVideoObjectFiles(directory)
    total_videos = len(video_files)
    
    if total_videos == 0:
        print(f"No video files found in directory: {directory}")
        return
    
    # Initialize scan metadata
    scan_start_time = datetime.now()
    scan_metadata = {
        'directory': directory,
        'total_files': total_videos,
        'start_time': scan_start_time.isoformat(),
        'platform': platform.system(),
        'ffmpeg_command': get_ffmpeg_command()
    }
    
    # Load existing state if resume is enabled
    processed_files = set()
    start_index = 1
    
    if resume:
        state_data = load_scan_state(directory)
        if state_data:
            processed_files = set(state_data.get('processed_files', []))
            start_index = len(processed_files) + 1
            print(f"Resuming scan from file {start_index} (found {len(processed_files)} already processed)")
            scan_metadata['resumed'] = True
            scan_metadata['resume_time'] = scan_start_time.isoformat()
        else:
            print("Starting new scan")
            scan_metadata['resumed'] = False
    else:
        print("Starting new scan (resume disabled)")
        scan_metadata['resumed'] = False
    
    # Setup output files
    timestamp = scan_start_time.strftime('%Y-%m-%d_%H-%M-%S')
    log_file_path = os.path.join(directory, f'{os.path.basename(directory.rstrip("/\\"))}_Logs.log')
    csv_file_path = os.path.join(directory, f'{os.path.basename(directory.rstrip("/\\"))}_Results.csv')
    
    if json_output:
        json_file_path = os.path.join(directory, f'{os.path.basename(directory.rstrip("/\\"))}_Results.json')
    
    # Initialize CSV file with headers if starting new scan
    if not resume or start_index == 1:
        with open(csv_file_path, 'w', newline='') as csvfile:
            fieldnames = ['File_Number', 'Filename', 'Full_Filepath', 'Corrupt']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
    
    # Get ffmpeg command
    ffmpeg_cmd = get_ffmpeg_command()
    if not ffmpeg_cmd:
        print("\nError: ffmpeg is required but not found on this system.")
        print("Please install ffmpeg:")
        print("  - On Ubuntu/Debian: sudo apt install ffmpeg")
        print("  - On CentOS/RHEL: sudo yum install ffmpeg") 
        print("  - On macOS: brew install ffmpeg")
        print("  - On Windows: Download from https://ffmpeg.org/download.html")
        return
    
    print(f"Using ffmpeg: {ffmpeg_cmd}")
    print(f"Scanning {total_videos} video files in: {directory}")
    print(f"Output files:")
    print(f"  Log: {log_file_path}")
    print(f"  CSV: {csv_file_path}")
    if json_output:
        print(f"  JSON: {json_file_path}")
    print("")
    
    # Initialize counters and results
    corrupt_files = []
    clean_files = []
    error_files = []
    json_results = []
    
    # Process video files
    for index, video in enumerate(video_files, 1):
        # Skip if already processed during resume
        if video.full_filepath in processed_files:
            continue
            
        if index < start_index:
            continue
        
        print(f"Processing {index}/{total_videos}: {video.filename}")
        
        file_start_time = time.time()
        is_corrupt = False
        ffmpeg_output = ""
        error_msg = ""
        
        try:
            # Prepare ffmpeg command with proper shell escaping
            if isWindowsOs():
                cmd = f'"{ffmpeg_cmd}" -v error -i "{video.full_filepath}" -f null - -hide_banner'
            else:
                cmd = f'{shlex.quote(ffmpeg_cmd)} -v error -i {shlex.quote(video.full_filepath)} -f null - -hide_banner'
            
            # Run ffmpeg
            if verbose:
                print(f"  Running: {cmd}")
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            ffmpeg_output = result.stderr.strip()
            
            # Determine if file is corrupt
            if result.returncode != 0 or ffmpeg_output:
                is_corrupt = True
                corrupt_files.append(video.full_filepath)
                status = "CORRUPT"
            else:
                clean_files.append(video.full_filepath)
                status = "CLEAN"
                
        except subprocess.TimeoutExpired:
            is_corrupt = True
            error_msg = "Processing timeout (>300s)"
            error_files.append(video.full_filepath)
            status = "ERROR (Timeout)"
        except Exception as e:
            is_corrupt = True
            error_msg = str(e)
            error_files.append(video.full_filepath)
            status = "ERROR"
        
        file_end_time = time.time()
        processing_time = file_end_time - file_start_time
        
        # Log results
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"File {index}: {video.filename}\n")
            log_file.write(f"Path: {video.full_filepath}\n")
            log_file.write(f"Status: {status}\n")
            log_file.write(f"Processing time: {processing_time:.2f}s\n")
            if ffmpeg_output:
                log_file.write(f"FFmpeg output: {ffmpeg_output}\n")
            if error_msg:
                log_file.write(f"Error: {error_msg}\n")
            log_file.write("-" * 50 + "\n")
        
        # Update CSV
        with open(csv_file_path, 'a', newline='') as csvfile:
            fieldnames = ['File_Number', 'Filename', 'Full_Filepath', 'Corrupt']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow({
                'File_Number': index,
                'Filename': video.filename,
                'Full_Filepath': video.full_filepath,
                'Corrupt': 'Yes' if is_corrupt else 'No'
            })
        
        # Store for JSON output
        if json_output:
            json_results.append({
                'file_number': index,
                'filename': video.filename,
                'full_filepath': video.full_filepath,
                'is_corrupt': is_corrupt,
                'status': status,
                'processing_time_seconds': round(processing_time, 2),
                'ffmpeg_output': ffmpeg_output,
                'error_message': error_msg
            })
        
        # Update processed files and save state
        processed_files.add(video.full_filepath)
        save_scan_state(directory, video_files, list(processed_files), scan_metadata)
        
        # Show progress
        progress = calculateProgress(index, total_videos)
        print(f"  Result: {status} ({processing_time:.1f}s) - Progress: {progress}%")
        
        if verbose and ffmpeg_output:
            print(f"  FFmpeg output: {ffmpeg_output}")
    
    # Calculate final statistics
    scan_end_time = datetime.now()
    total_duration = (scan_end_time - scan_start_time).total_seconds()
    processed_count = len(processed_files)
    corrupt_count = len(corrupt_files)
    clean_count = len(clean_files)
    error_count = len(error_files)
    
    # Print summary
    print("\n" + "="*60)
    print("SCAN COMPLETE")
    print("="*60)
    print(f"Directory: {directory}")
    print(f"Total files found: {total_videos}")
    print(f"Files processed: {processed_count}")
    print(f"Corrupt files: {corrupt_count}")
    print(f"Clean files: {clean_count}")
    print(f"Error files: {error_count}")
    print(f"Corruption rate: {(corrupt_count/processed_count*100):.1f}%" if processed_count > 0 else "N/A")
    print(f"Scan duration: {convertTime(int(total_duration))}")
    print(f"Average per file: {(total_duration/processed_count):.1f}s" if processed_count > 0 else "N/A")
    
    # Generate JSON output if requested
    if json_output:
        scan_metadata.update({
            'end_time': scan_end_time.isoformat(),
            'total_duration_seconds': round(total_duration, 2),
            'files_processed': processed_count,
            'corrupt_files': corrupt_count,
            'clean_files': clean_count,
            'error_files': error_count,
            'corruption_rate_percent': round(corrupt_count/processed_count*100, 2) if processed_count > 0 else 0,
            'average_processing_time_seconds': round(total_duration/processed_count, 2) if processed_count > 0 else 0
        })
        
        json_data = {
            'scan_metadata': scan_metadata,
            'results': json_results,
            'summary': {
                'total_files_found': total_videos,
                'files_processed': processed_count,
                'corrupt_files': corrupt_count,
                'clean_files': clean_count,
                'error_files': error_count,
                'corruption_rate_percent': round(corrupt_count/processed_count*100, 2) if processed_count > 0 else 0,
                'scan_duration_formatted': convertTime(int(total_duration)),
                'average_processing_time_seconds': round(total_duration/processed_count, 2) if processed_count > 0 else 0
            }
        }
        
        with open(json_file_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"\nDetailed results saved to: {json_file_path}")
    
    # Clean up state file on successful completion
    if processed_count == total_videos:
        state_file = get_state_file_path(directory)
        try:
            if os.path.exists(state_file):
                os.remove(state_file)
                print("Scan state file cleaned up.")
        except Exception as e:
            print(f"Warning: Could not remove state file: {e}")

def parse_cli_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Corrupt Video Inspector - Scan directories for corrupt video files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python CorruptVideoInspector.py                          # Run GUI mode
  python CorruptVideoInspector.py /path/to/videos          # Run CLI mode
  python CorruptVideoInspector.py --no-resume /path/videos # CLI without resume
  python CorruptVideoInspector.py --verbose /path/videos   # CLI with verbose output
  python CorruptVideoInspector.py --json /path/videos      # CLI with JSON output
  python CorruptVideoInspector.py --list-videos /path      # List videos only
        ''')
    
    parser.add_argument('directory', 
                       nargs='?',
                       help='Directory to scan for video files (if not provided, GUI mode will start)')
    
    parser.add_argument('--verbose', '-v', 
                       action='store_true',
                       help='Enable verbose output showing FFmpeg details')
    
    parser.add_argument('--no-resume', 
                       action='store_true',
                       help='Disable automatic resume functionality (start from beginning)')
    
    parser.add_argument('--list-videos', '-l', 
                       action='store_true',
                       help='List all video files in directory without scanning')
    
    parser.add_argument('--json', '-j', 
                       action='store_true',
                       help='Generate JSON output file with detailed scan results')
    
    parser.add_argument('--version', 
                       action='version', 
                       version='Corrupt Video Inspector v2.0')
    
    return parser.parse_args()

def run_cli_mode(args):
    """Run the application in CLI mode"""
    directory = os.path.abspath(args.directory)
    
    # Validate directory
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' does not exist or is not a directory.")
        sys.exit(1)
    
    # Handle list-videos option
    if args.list_videos:
        print(f'Scanning directory: {directory}')
        video_files = getAllVideoObjectFiles(directory)
        total_count = len(video_files)
        
        if total_count == 0:
            print('No video files found in the specified directory.')
        else:
            print(f'\nFound {total_count} video files:')
            for i, video in enumerate(video_files, 1):
                print(f'  {i:3d}: {video.filename}')
        return
    
    # Check if directory has video files
    total_videos = countAllVideoFiles(directory)
    if total_videos == 0:
        print(f"No video files found in directory: {directory}")
        sys.exit(1)
    
    # Check ffmpeg availability first
    ffmpeg_cmd = get_ffmpeg_command()
    if not ffmpeg_cmd:
        print("\nError: ffmpeg is required but not found on this system.")
        print("Please install ffmpeg:")
        print("  - On Ubuntu/Debian: sudo apt install ffmpeg")
        print("  - On CentOS/RHEL: sudo yum install ffmpeg")
        print("  - On macOS: brew install ffmpeg")
        print("  - On Windows: Download from https://ffmpeg.org/download.html")
        sys.exit(1)
    
    print(f'Starting video corruption scan...')
    print(f'Platform: {platform.system()}')
    print(f'Using ffmpeg: {ffmpeg_cmd}')
    
    # Start the inspection
    resume_enabled = not args.no_resume
    inspect_video_files_cli(directory, resume=resume_enabled, verbose=args.verbose, json_output=args.json)

# ========================= MAIN ==========================

if __name__ == '__main__':
    # Parse command line arguments
    args = parse_cli_arguments()
    
    # If directory is provided, run in CLI mode
    if args.directory:
        run_cli_mode(args)
    else:
        # Run in GUI mode
        if not TKINTER_AVAILABLE:
            print("Error: tkinter is not available. GUI mode requires tkinter.")
            print("Please install tkinter or use CLI mode by providing a directory argument.")
            print("Example: python CorruptVideoInspector.py /path/to/videos")
            sys.exit(1)
        
        root = tk.Tk()
        root.title("Corrupt Video Inspector")
        if isMacOs():
            root.geometry("500x650")
        if isWindowsOs():
            root.geometry("500x750")
            icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'icon.ico'))
            root.iconbitmap(default=icon_path)
        if isLinuxOs():
            root.geometry("500x750")
        g_progress = tk.StringVar()
        g_count = tk.StringVar()
        g_currently_processing = tk.StringVar()
        g_mac_pid = ''
        g_windows_pid = ''

        label_select_directory = tk.Label(root, wraplength=450, justify="left", text="Select a directory to search for all video files within the chosen directory and all of its containing subdirectories", font=('Helvetica', 16))
        label_select_directory.pack(fill=tk.X, pady=20, padx=20)

        button_select_directory = tk.Button(root, text="Select Directory", width=20, command=lambda: selectDirectory(root, label_select_directory, button_select_directory))
        button_select_directory.pack(pady=20)

        root.mainloop()
"""
Utility functions for Corrupt Video Inspector
Contains platform detection, time conversion, file handling utilities, and other helper functions.
"""
import os
import platform

# Video file extensions supported by the inspector
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', '.webm', '.m4v', '.m4p', '.mpeg', '.mpg', '.3gp', '.3g2']


def is_macos():
    """Check if the current platform is macOS"""
    return 'Darwin' in platform.system()


def is_windows_os():
    """Check if the current platform is Windows"""
    return 'Windows' in platform.system()


def is_linux_os():
    """Check if the current platform is Linux"""
    return 'Linux' in platform.system()


def convert_time(seconds):
    """Convert seconds to HH:MM:SS format"""
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)


def truncate_filename(input_filename):
    """Truncate filename for display purposes based on platform"""
    file_name, file_extension = os.path.splitext(input_filename)
    if is_macos() and len(file_name) > 50:
        truncated_string = file_name[0:49]
        return f'{truncated_string}..{file_extension}'
    elif is_windows_os() and len(file_name) > 42:
        truncated_string = file_name[0:41]
        return f'{truncated_string}..{file_extension}'
    else:
        return input_filename


def count_all_video_files(directory):
    """Count all video files in directory and subdirectories"""
    total = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(tuple(VIDEO_EXTENSIONS)):
                total += 1
    return total


def get_all_video_files(directory):
    """Get list of all video files with index numbers for display"""
    videos_found_list = []
    for root, dirs, files in os.walk(directory):
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


def calculate_progress(count, total):
    """Calculate percentage progress"""
    return "{0}%".format(int((count / total) * 100))


def estimated_time(total_videos):
    """Estimate processing time based on number of videos"""
    # estimating 3 mins per 2GB video file, on average
    total_minutes = total_videos * 3
    # Get hours with floor division
    hours = total_minutes // 60
    # Get additional minutes with modulus
    minutes = total_minutes % 60
    # Create time as a string
    time_string = "{} hours, {} minutes".format(hours, minutes)
    return time_string
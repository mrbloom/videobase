import time

import progressbar
import threading
import os
import ffmpeg
import shutil  # Add this import for the disk_usage function

import threading
import glob
import subprocess


class FFmpegThread(threading.Thread):
    def __init__(self, input_video_path, output_video_path, input_keys={}, output_keys={}, *args, **kwargs):
        super(FFmpegThread, self).__init__(*args, **kwargs)
        self.input_video_path = input_video_path
        self.output_video_path = output_video_path
        self.input_keys = input_keys
        self.output_keys = output_keys
        self.progress_bar = progressbar.ProgressBar(max_value=1.0, widgets=[
            ' [', progressbar.Timer(), '] ',
            progressbar.Bar(),
            ' (', progressbar.ETA(), ') ',
        ])
        self.required_space_gb = 1.0

    def check_disk_space(self, path):
        """Check available disk space where the file is located."""
        # Use disk_usage for cross-platform support
        total, used, free = shutil.disk_usage(path)
        free_gb = free / (1024 ** 3)
        return free_gb

    def enough_disk_space(self,path,required_space_gb):
        output_directory = os.path.dirname(path)
        try:
            disk_space = self.check_disk_space(output_directory)
            if disk_space < required_space_gb:
                print(f"Not enough space on the disk at {output_directory}. Required: {self.required_space_gb}GB.")
                return False
        except FileNotFoundError:
            # Splitting by os.sep will provide us the list of folders in the path
            parts = path.split(os.sep)

            # For Windows, it will return the drive. For Linux/Mac, it will return the first folder.
            disk_letter = parts[0] if parts else None
            disk_space = self.check_disk_space(os.path.join(disk_letter, os.sep))
            if disk_space < required_space_gb:
                return False
        return True

    def run(self):
        # Check if there's enough space on the disk
        output_directory = os.path.dirname(self.output_video_path)
        if not self.enough_disk_space(self.output_video_path, self.required_space_gb):
            print(f"Not enough space on the disk at {output_directory}. Required: {self.required_space_gb}GB.")
            return
            # Get total duration of video
        probe = ffmpeg.probe(self.input_video_path)
        duration = float(probe['streams'][0]['duration'])

        # Use input_keys and output_keys
        out, _ = (
            ffmpeg
            .input(self.input_video_path, **self.input_keys)
            .output(self.output_video_path, **self.output_keys, vcodec='h264', video_bitrate='1.5M')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        for line in out.decode('utf-8').split('\n'):
            # Get current time from ffmpeg output and update progress bar
            if 'time=' in line:
                time_encoded = float(line.split('time=')[1].split(' ')[0])
                self.progress_bar.update(time_encoded / duration)
        self.progress_bar.finish()


# thread = FFmpegThread(
#     "input_video.mp4",
#     "output_video.mp4",
#     input_keys={"an": None},  # Example: Disable audio input stream
#     output_keys={"an": None}  # Example: Disable audio output stream
# )
# thread.start()




class FFMPEGConverter:
    def __init__(self, ffmpeg_path, num_threads, start_delay,input_folder, output_folder, file_mask,
                 codec='h264', bitrate='1.5M'):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.file_mask = file_mask
        self.num_threads = num_threads
        self.codec = codec
        self.bitrate = bitrate
        self.start_delay = start_delay

        # Check FFmpeg installation
        self.ffmpeg_path = ffmpeg_path
        if not ffmpeg_path and not self.is_ffmpeg_installed():
            raise ValueError("FFmpeg not found in system path and no alternative path provided.")

    def is_ffmpeg_installed(self):
        """Checks if FFmpeg is installed and accessible from the command line."""
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except Exception:
            return False

    def update_system_path(self):
        """Adds the FFmpeg binary location to the system PATH."""
        if self.ffmpeg_path:
            os.environ["PATH"] += os.pathsep + os.path.dirname(self.ffmpeg_path)
    def convert(self):
        files_to_convert = glob.glob(os.path.join(self.input_folder, '**', self.file_mask), recursive=True)
        self.update_system_path()
        threads = []

        for file_path in files_to_convert:
            rel_path = os.path.relpath(file_path, self.input_folder)
            output_path = os.path.join(self.output_folder, rel_path)

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            thread = FFmpegThread(file_path, output_path,
                                  output_keys={'vcodec': self.codec, 'video_bitrate': self.bitrate},
                                  ffmpeg_path=self.ffmpeg_path)
            threads.append(thread)

            thread.start()
            time.sleep(self.start_delay)

            # If we've reached the max number of threads, wait for one to finish
            while threading.active_count() > self.num_threads:
                time.sleep(1)  # Check every second if a thread has finished

        # No need to join all threads at the end since we ensure the max thread count throughout the process.

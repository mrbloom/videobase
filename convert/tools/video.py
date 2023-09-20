import sys
import time

import progressbar
import threading
import os
import ffmpeg
import shutil  # Add this import for the disk_usage function

import threading
import glob
import subprocess

import dropbox
import json



class FFmpegThread(threading.Thread):
    active_ffmpeg_threads = 0
    def __init__(self, input_video_path, output_video_path, input_keys={}, output_keys={}, *args, **kwargs):
        super(FFmpegThread, self).__init__(*args, **kwargs)
        self.input_video_path = input_video_path
        self.output_video_path = output_video_path
        self.input_keys = input_keys
        self.output_keys = output_keys
        self.source_filename = os.path.basename(input_video_path)
        self.encoded_filename = os.path.basename(output_video_path)
        self.progress_bar = progressbar.ProgressBar( max_value=1.0, widgets=[
              # Title with filenames
            f"{self.source_filename}=>{self.encoded_filename} ",
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
        FFmpegThread.active_ffmpeg_threads += 1
        # Check if there's enough space on the disk
        output_directory = os.path.dirname(self.output_video_path)
        if not self.enough_disk_space(self.output_video_path, self.required_space_gb):
            print(f"Not enough space on the disk at {output_directory}. Required: {self.required_space_gb}GB.")
            return
        # Get total duration of video
        probe = ffmpeg.probe(self.input_video_path)
        duration = float(probe['streams'][0]['duration'])

        # Use ffmpeg-python to build the FFmpeg command
        stream = (
            ffmpeg
            .input(self.input_video_path, **self.input_keys)
            .output(self.output_video_path, **self.output_keys)
            .overwrite_output()
            .compile()
        )

        # Run the command using subprocess
        process = subprocess.Popen(stream, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        for line in iter(process.stdout.readline, ''):
            # Get current time from ffmpeg output and update progress bar
            if 'time=' in line:
                time_encoded_str = line.split('time=')[1].split(' ')[0]
                time_encoded = self.time_to_seconds(time_encoded_str)
                self.progress_bar.update(time_encoded / duration)
        process.stdout.close()
        process.wait()
        self.progress_bar.finish()

        FFmpegThread.active_ffmpeg_threads -= 1

    def time_to_seconds(self, time_str, sep=':'):
        h, m, s = time_str.split(sep)
        return int(h) * 3600 + int(m) * 60 + float(s)


class FFMPEGDropboxThread(FFmpegThread):
    CHUNK_SIZE = 1024 * 1024 * 10  # 10MB chunks

    def __init__(self,access_token, dropbox_path, output_video_path, input_keys={}, output_keys={}, *args, **kwargs):

        self.access_token = access_token
        self.dropbox_path = dropbox_path
        self.dbx = dropbox.Dropbox(self.access_token) if access_token else None
        input_video_path = self.dropbox_download()

        super(FFMPEGDropboxThread, self).__init__( input_video_path, output_video_path, input_keys, output_keys, *args, **kwargs)  # Set input to None

        # Fetch the video from Dropbox
        # metadata, response = self.dbx.files_download(self.dropbox_path)
        #
        # # Update the FFmpeg command to read data from stdin
        # stream = (
        #     ffmpeg
        #     .input('pipe:', format=self.input_format, **self.input_keys)  # Assume format is mp4 for this example
        #     .output(self.output_video_path, **self.output_keys)
        #     .overwrite_output()
        #     .compile()
        # )
        #
        # # Start FFmpeg and pipe in the content
        # process = subprocess.Popen(stream, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #
        # duration = 0
        # for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
        #     if duration == 0:
        #         duration = self.get_duration_from_chunk(chunk)
        #         print(f"Duration of {self.dropbox_path} = {duration}")
        #     process.stdin.write(chunk)
        #
        # process.stdin.close()
        # if duration:
        #     self.progress_bar(process,duration)

    # def progress_bar(self,process,duration):
    #     for line in iter(process.stdout.readline, ''):
    #         # Print FFmpeg's output to the console
    #         print(line.strip())
    #         # Get current time from ffmpeg output and update progress bar
    #         if 'time=' in line:
    #             time_encoded_str = line.split('time=')[1].split(' ')[0]
    #             time_encoded = self.time_to_seconds(time_encoded_str)
    #             self.progress_bar.update(time_encoded / duration)
    #
    #     process.stdout.close()
    #     process.wait()
    #     self.progress_bar.finish()
    #
    # def get_duration_from_chunk(self, data_chunk):
    #     # Use ffmpeg-python to probe the video duration
    #     try:
    #         probe = ffmpeg.probe("pipe:", input=data_chunk, show_format=True, show_streams=True)
    #     except:
    #         print("Error with probe thats try to get duration.")
    #         return None
    #     # Extract the duration from the appropriate stream (video stream)
    #     for stream in probe.get('streams', []):
    #         if stream['codec_type'] == 'video':
    #             return float(stream['duration'])
    #     return None

    def dropbox_download(self):
        # Fetch metadata of the video from Dropbox
        metadata = self.dbx.files_get_metadata(self.dropbox_path)
        file_size = metadata.size

        # Initialize progress bar
        progress = progressbar.ProgressBar(max_value=file_size, widgets=[
            'Downloading: ',
            progressbar.Percentage(),
            ' ',
            progressbar.Bar(marker=progressbar.RotatingMarker()),
            ' ',
            progressbar.ETA(),
            ' ',
            progressbar.FileTransferSpeed()
        ])

        # Fetch the video from Dropbox
        _, response = self.dbx.files_download(self.dropbox_path)

        # Save the video to a temporary file and update the progress bar
        downloaded_size = 0
        temp_filename = f"temp_{os.path.basename(self.dropbox_path)}"
        with open(temp_filename, 'wb') as temp_file:
            for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                downloaded_size += len(chunk)
                progress.update(downloaded_size)
                temp_file.write(chunk)

        # Finish the progress bar
        progress.finish()
        return temp_filename






class FFMPEGConverter:
    def __init__(self, ffmpeg_path, num_threads, start_delay,input_folder, output_folder, file_mask,
                 codec='h264', bitrate='1.5M', output_ext='mp4'):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.file_mask = file_mask
        self.num_threads = num_threads
        self.codec = codec
        self.bitrate = bitrate
        self.start_delay = start_delay
        self.output_ext = output_ext

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
            output_path = self.change_file_extension( os.path.join(self.output_folder, rel_path) )

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            thread = FFmpegThread(file_path, output_path,
                                  output_keys={'vcodec': self.codec, 'video_bitrate': self.bitrate})
            threads.append(thread)

            thread.start()
            time.sleep(self.start_delay)

            # If we've reached the max number of threads, wait for one to finish
            while FFmpegThread.active_ffmpeg_threads >= self.num_threads:
                time.sleep(1)  # Check every second if a thread has finished

        # No need to join all threads at the end since we ensure the max thread count throughout the process.

    def change_file_extension(self, filepath):
        """
        Change the file extension of a given filepath.

        Args:
        - filepath (str): The original file path.
        - new_extension (str): The new extension (e.g., 'mp4', 'txt'). Do not include the dot.

        Returns:
        - str: The filepath with the changed extension.
        """
        base = os.path.splitext(filepath)[0]
        return f"{base}.{self.output_ext}"






class FFMPEGDropboxConverter:
    def __init__(self, access_token, ffmpeg_path, num_threads, start_delay, dropbox_folder, local_temp_folder,
                 output_folder, file_mask,
                 codec='h264', bitrate='1.5M', output_ext='mp4'):

        self.access_token = access_token
        self.dbx = dropbox.Dropbox(self.access_token) if access_token else None

        self.dropbox_folder = dropbox_folder
        self.local_temp_folder = local_temp_folder  # A local folder where Dropbox files will be temporarily stored
        self.output_folder = output_folder
        self.file_mask = file_mask
        self.num_threads = num_threads
        self.codec = codec
        self.bitrate = bitrate
        self.start_delay = start_delay
        self.output_ext = output_ext

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
        # List all files in the Dropbox folder with the given mask
        files_to_convert = self.list_dropbox_files(self.dropbox_folder, self.file_mask)
        self.update_system_path()
        threads = []

        for dropbox_path in files_to_convert:
            local_temp_path = os.path.join(self.local_temp_folder, os.path.basename(dropbox_path))
            output_path = os.path.join(self.output_folder, self.change_file_extension(os.path.basename(dropbox_path)))

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            thread = FFMPEGDropboxThread(self.access_token, dropbox_path, local_temp_path, output_path,
                                         output_keys={'vcodec': self.codec, 'video_bitrate': self.bitrate})
            threads.append(thread)

            thread.start()
            time.sleep(self.start_delay)

            # If we've reached the max number of threads, wait for one to finish
            while FFmpegThread.active_ffmpeg_threads >= self.num_threads:
                time.sleep(1)  # Check every second if a thread has finished

    def list_dropbox_files(self, folder_path, file_mask):
        """List all files in the Dropbox folder with the given mask."""
        results = []
        for entry in self.dbx.files_list_folder(folder_path).entries:
            if isinstance(entry, dropbox.files.FileMetadata) and entry.name.endswith(file_mask):
                results.append(entry.path_display)
        return results

    def change_file_extension(self, filepath):
        base = os.path.splitext(filepath)[0]
        return f"{base}.{self.output_ext}"

# Example usage:
# thread = FFMPEGDropboxThread(
#     access_token="YOUR_ACCESS_TOKEN",
#     dropbox_path="/path_to_video_on_dropbox/video.mp4",
#     output_video_path="encoded_video.mp4"
# )
# thread.start()


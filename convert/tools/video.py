import time
import threading
import os
import ffmpeg
import shutil
import glob
import subprocess
import dropbox
import re

from tqdm import tqdm  # Import tqdm

class ConfigFFmpeg:
    def __init__(self, input, output, input_keys={}, output_keys={}):
        self.input = input
        self.output = output
        self.input_keys = input_keys
        self.output_keys = output_keys


class ConfigDropboxFFmpeg(ConfigFFmpeg):
    def __init__(self,dropbox_input, dropbox_output, access_token, input, output, input_keys={}, output_keys={}):
        self.dropbox_input = dropbox_input
        self.dropbox_output = dropbox_output
        self.access_token = access_token
        super().__init__(input, output, input_keys, output_keys)

    def to_ConfigFFmpeg(self):
        """Cast the ConfigDropboxFFmpeg object to ConfigFFmpeg"""
        return ConfigFFmpeg(self.input, self.output, self.input_keys, self.output_keys)

class FFmpegThread(threading.Thread):
    active_ffmpeg_threads = 0

    def __init__(self, config:ConfigFFmpeg, *args, **kwargs):
        super(FFmpegThread, self).__init__(*args, **kwargs)
        self.config = config
        self.source_filename = os.path.basename(config.input)
        self.encoded_filename = os.path.basename(config.output)
        self.progress_bar = None
        self.required_space_gb = 1.0


    def run(self):
        FFmpegThread.active_ffmpeg_threads += 1

        # Check if there's enough space on the disk
        if not self.enough_disk_space(self.config.output, self.required_space_gb):
            print(f"Not enough space on the disk at {self.config.output}. Required: {self.required_space_gb}GB.")
            return

        # Get total duration of video
        probe = ffmpeg.probe(self.config.input)
        duration = float(probe['streams'][0]['duration'])

        # Use ffmpeg-python to build the FFmpeg command
        stream = (
            ffmpeg
            .input(self.config.input, **self.config.input_keys)
            .output(self.config.output, **self.config.output_keys)
            .overwrite_output()
            .compile()
        )

        # Run the command using subprocess
        process = subprocess.Popen(stream, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        # Initialize tqdm progress bar
        self.progress_bar = tqdm(total=duration, desc=f"Converting {self.source_filename}=>{self.encoded_filename}",
                                 bar_format="{desc}: {percentage:.1f}% |{bar}| {elapsed} < {remaining}")
        self.show_progress(process)

        FFmpegThread.active_ffmpeg_threads -= 1

    def enough_disk_space(self, path, required_space_gb):
        total, used, free = shutil.disk_usage(os.path.split(path)[0])
        disk_space = free / (1024 ** 3)
        if disk_space < required_space_gb:
            return False
        return True

    def show_progress(self, process):
        for line in iter(process.stdout.readline, ''):
            if 'time=' in line:
                time_encoded_str = line.split('time=')[1].split(' ')[0]
                time_encoded = self.time_to_seconds(time_encoded_str)
                self.progress_bar.update(time_encoded - self.progress_bar.n)
        process.stdout.close()
        process.wait()
        self.progress_bar.close()

    def time_to_seconds(self, time_str, sep=':'):
        h, m, s = time_str.split(sep)
        return int(h) * 3600 + int(m) * 60 + float(s)


class FFMPEGDropboxThread(FFmpegThread):
    CHUNK_SIZE = 1024 * 1024 * 10  # 10MB chunks

    def __init__(self, config:ConfigDropboxFFmpeg, *args, **kwargs):
        self.config = config
        self.dbx = dropbox.Dropbox(self.config.access_token)
        self.dropbox_download()

        super(FFMPEGDropboxThread, self).__init__( config.to_ConfigFFmpeg(),*args, **kwargs)  # Set input to None

    def dropbox_download(self):
        # Fetch metadata of the video from Dropbox
        metadata = self.dbx.files_get_metadata(self.config.dropbox_input)
        file_size = metadata.size

        # Initialize tqdm progress bar for downloading
        progress = tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Downloading {self.config.dropbox_input}=>{self.config.input}")

        # Fetch the video from Dropbox
        _, response = self.dbx.files_download(self.config.dropbox_input)

        # Save the video to a temporary file and update the progress bar
        temp_filename = self.config.input
        with open(temp_filename, 'wb') as temp_file:
            for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                progress.update(len(chunk))
                temp_file.write(chunk)

        progress.close()

    def run(self):
        super().run()
        print(f"Delete the temporary Dropbox file after processing {self.config.input}")
        os.remove(self.config.input)


class FileConverter:
    def __init__(self, ffmpeg_path, num_threads, start_delay, codec='h264', bitrate='1.5M', output_ext='mp4'):
        self.num_threads = num_threads
        self.codec = codec
        self.bitrate = bitrate
        self.start_delay = start_delay
        self.output_ext = output_ext
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

    def change_file_extension(self, filepath, ext=None):
        base = os.path.splitext(filepath)[0]
        if ext:
            return f"{base}.{ext}"
        return f"{base}.{self.output_ext}"

    def convert(self):
        raise NotImplementedError("Subclasses must implement this method")

    def make_output_path(self,file_path,start_folder,output_folder):
        rel_path = os.path.relpath(file_path, start_folder)
        output_path = self.change_file_extension(os.path.join(output_folder, rel_path))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        return output_path


class FFMPEGConverter(FileConverter):
    def __init__(self, ffmpeg_path, num_threads, start_delay, input_folder, output_folder, file_mask, *args, **kwargs):
        super().__init__(ffmpeg_path, num_threads, start_delay, *args, **kwargs)
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.file_mask = file_mask


    def convert(self):
        files_to_convert = glob.glob(os.path.join(self.input_folder, '**', self.file_mask), recursive=True)
        self.update_system_path()
        threads = []

        for file_path in files_to_convert:
            output_path = self.make_output_path(file_path, self.input_folder,self.output_folder)
            config = ConfigFFmpeg(file_path, output_path, {},
                                  {
                                      'vcodec': self.codec,
                                      'video_bitrate': self.bitrate
                                  })
            thread = FFmpegThread(config)
            threads.append(thread)
            thread.start()
            time.sleep(self.start_delay)

            while FFmpegThread.active_ffmpeg_threads >= self.num_threads:
                time.sleep(1)


class FFMPEGDropboxConverter(FileConverter):
    def __init__(self, dropbox_input, dropbox_output, access_token, ffmpeg_path, num_threads, start_delay, input_folder,
                 output_folder, file_mask, *args, **kwargs):
        super().__init__(ffmpeg_path, num_threads, start_delay, *args, **kwargs)
        self.access_token = access_token
        self.dbx = dropbox.Dropbox(self.access_token) if access_token else None
        self.file_mask = file_mask
        self.dropbox_input = dropbox_input
        self.dropbox_output = dropbox_output
        self.input_folder = input_folder
        self.output_folder = output_folder

    def convert(self):
        files_to_convert = self.list_dropbox_files(self.dropbox_input, self.file_mask)
        self.update_system_path()
        threads = []

        for dropbox_path in files_to_convert:
            output_path = self.make_output_path(dropbox_path,self.dropbox_input,self.output_folder)
            config = ConfigDropboxFFmpeg(dropbox_path,
                                         "",
                                         self.access_token,
                                         self.change_file_extension(output_path,"ts"),
                                         output_path,
                                         {},
                                         {'vcodec': self.codec, 'video_bitrate': self.bitrate}

            )
            thread = FFMPEGDropboxThread(config)
            threads.append(thread)
            thread.start()
            time.sleep(self.start_delay)

            while FFmpegThread.active_ffmpeg_threads >= self.num_threads:
                time.sleep(1)

    def list_dropbox_files(self, folder_path, file_mask):
        # Convert file_mask (wildcard pattern) to regex pattern
        pattern = re.compile(file_mask.replace('.', r'\.').replace('*', '.*') + '$')

        results = []

        # Initialize with the first call
        result = self.dbx.files_list_folder(folder_path, recursive=True)

        while True:
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata) and pattern.match(entry.name):
                    results.append(entry.path_lower)

            # Check if there are more paginated results
            if not result.has_more:
                break

            # If there are more results, continue fetching them
            result = self.dbx.files_list_folder_continue(result.cursor)

        return results






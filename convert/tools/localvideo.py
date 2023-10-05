import glob
import os
import shutil
import time
import threading
import ffmpeg
import subprocess
from dataclasses import dataclass
from tqdm import tqdm
import shlex

# Constants
BYTES_IN_GB = 1024 ** 3


@dataclass
class ConfigFFmpeg:
    input: str
    output: str
    input_keys: dict
    output_keys: dict

    @staticmethod
    def parse_ffmpeg_keys(keys_str):
        tokens = shlex.split(keys_str)

        if len(tokens) % 2 != 0:  # The number of tokens should be even (key-value pairs)
            raise ValueError("The provided keys string seems to be invalid or incomplete.")

        keys_dict = {}
        for i in range(0, len(tokens), 2):  # Step by 2 for key-value pairs
            key = tokens[i].lstrip('-')  # Remove the leading dash from the key
            value = tokens[i + 1]
            keys_dict[key] = value

        return keys_dict


@dataclass
class ConfigFFMPEGConverter:
    ffmpeg_path: str
    num_threads: int
    start_delay: int
    input_folder: str
    output_folder: str
    file_mask: str
    video_codec: str
    video_bitrate: str
    output_ext: str
    input_keys_str: str


class FFmpegThread(threading.Thread):
    active_ffmpeg_threads = 0

    def __init__(self, config: ConfigFFmpeg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.source_filename = os.path.basename(config.input)
        self.encoded_filename = os.path.basename(config.output)
        self.progress_bar = None
        self.required_space_gb = 1.0

    def run(self):
        FFmpegThread.active_ffmpeg_threads += 1
        if not self.enough_disk_space(self.config.output, self.required_space_gb):
            print(f"Not enough space on disk at {self.config.output}. Required: {self.required_space_gb}GB.")
            return
        # Get total duration of video
        probe = ffmpeg.probe(self.config.input)
        duration = float(probe['streams'][0]['duration'])
        # .\ffmpeg -hwaccel cuda -hwaccel_output_format cuda -i "%~1" -c:a copy -c:v h264_nvenc -y -b:v 1.5M   "%~2"
        # Use ffmpeg-python to build the FFmpeg comm
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
        _, _, free = shutil.disk_usage(os.path.split(path)[0])
        return free >= required_space_gb * BYTES_IN_GB

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


class FileConverter:
    def __init__(self, ffmpeg_path, num_threads, start_delay, output_ext):
        self.num_threads = num_threads
        self.start_delay = start_delay
        self.output_ext = output_ext
        self.ffmpeg_path = ffmpeg_path
        self.check_ffmpeg_install()

    def check_ffmpeg_install(self):
        if not self.ffmpeg_path and not self.is_ffmpeg_installed():
            raise ValueError("FFmpeg not found in system path and no alternative path provided.")
        if self.ffmpeg_path:
            os.environ["PATH"] += os.pathsep + os.path.dirname(self.ffmpeg_path)

    @staticmethod
    def is_ffmpeg_installed():
        """Checks if FFmpeg is installed."""
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except Exception:
            return False

    @staticmethod
    def change_file_extension(filepath, ext):
        return f"{os.path.splitext(filepath)[0]}.{ext}"

    def convert(self):
        raise NotImplementedError("Subclasses must implement this method.")

    def make_output_path(self, file_path, start_folder, output_folder):
        rel_path = os.path.relpath(file_path, start_folder)
        ext = self.config.file_mask.split('.')[-1]
        output_path = self.change_file_extension(os.path.join(output_folder, rel_path), ext)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        return output_path


class FFMPEGConverter(FileConverter):
    def __init__(self, config):
        super().__init__(config.ffmpeg_path, config.num_threads, config.start_delay, config.output_ext)
        self.config = config

    def convert(self):
        files_to_convert = glob.glob(os.path.join(self.config.input_folder, '**', self.config.file_mask),
                                     recursive=True)
        threads = []
        input_keys = ConfigFFmpeg.parse_ffmpeg_keys(self.config.input_keys_str)
        for file_path in files_to_convert:
            output_path = self.make_output_path(file_path, self.config.input_folder, self.config.output_folder)
            config = ConfigFFmpeg(file_path, output_path, input_keys,
                                  {
                                      'vcodec': self.config.video_codec,
                                      'video_bitrate': self.config.video_bitrate
                                  })
            thread = FFmpegThread(config)
            threads.append(thread)
            thread.start()
            time.sleep(self.start_delay)

            while FFmpegThread.active_ffmpeg_threads >= self.num_threads:
                time.sleep(1)

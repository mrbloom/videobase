import os
import time
import threading
import dropbox
import re
from dataclasses import dataclass
from tqdm import tqdm
from .localvideo import ConfigFFmpeg, FFmpegThread, FileConverter

CHUNK_SIZE = 1024 * 1024 * 10  # 10MB chunks

@dataclass
class ConfigDropboxFFmpeg(ConfigFFmpeg):
    dropbox_input: str
    dropbox_output: str
    access_token: str

    def to_ConfigFFmpeg(self):
        """Converts the ConfigDropboxFFmpeg object to ConfigFFmpeg."""
        return ConfigFFmpeg(self.input, self.output, self.input_keys, self.output_keys)

class FFMPEGDropboxThread(FFmpegThread):
    def __init__(self, config: ConfigDropboxFFmpeg, *args, **kwargs):
        super().__init__(config.to_ConfigFFmpeg(), *args, **kwargs)
        self.dbx = dropbox.Dropbox(config.access_token)
        self.dropbox_download()

        super(FFMPEGDropboxThread, self).__init__(config.to_ConfigFFmpeg(), *args, **kwargs)  # Set input to None

    def dropbox_download(self):
        # Fetch metadata of the video from Dropbox
        metadata = self.dbx.files_get_metadata(self.config.dropbox_input)
        file_size = metadata.size

        # Initialize tqdm progress bar for downloading
        progress = tqdm(total=file_size, unit='B', unit_scale=True,
                        desc=f"Downloading {self.config.dropbox_input}=>{self.config.input}")

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

@dataclass
class ConfigFFMPEGDropboxConverter:
    ffmpeg_path: str
    num_threads: int
    start_delay: int
    input_folder: str
    output_folder: str
    file_mask: str
    video_codec: str
    video_bitrate: str
    output_ext: str
    access_token: str
    dropbox_input: str
    dropbox_output: str

class FFMPEGDropboxConverter(FileConverter):
    def __init__(self, config):
        super().__init__(config.ffmpeg_path, config.num_threads, config.start_delay, config.video_codec,
                         config.video_bitrate, config.output_ext)
        self.config = config

    def convert(self):
        files_to_convert = self.list_dropbox_files(self.config.dropbox_input, self.config.file_mask)
        self.update_system_path()
        threads = []

        for dropbox_path in files_to_convert:
            output_path = self.make_output_path(dropbox_path, self.config.dropbox_input, self.config.output_folder)
            _, file_extension = os.path.splitext(self.config.file_mask)
            config = ConfigDropboxFFmpeg(
                dropbox_path, "", self.config.access_token,
                self.change_file_extension(output_path, file_extension, output_path),
                {},
                {'vcodec': self.config.video_codec, 'video_bitrate': self.config.video_bitrate}
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

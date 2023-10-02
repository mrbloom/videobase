import os
import shutil
import time
import threading
import dropbox
import re
from dataclasses import dataclass
from tqdm import tqdm

CHUNK_SIZE = 1024 * 1024 * 10  # 10MB chunks


class DropboxDownload(threading.Thread):
    active_download_threads = 0
    def __init__(self, access_token, dropbox_path, download_path, download_sufix="downloading"):
        super().__init__()
        self.access_token = access_token
        self.dropbox_path = dropbox_path
        self.download_path = download_path
        self.download_sufix = download_sufix
        self.dbx = dropbox.Dropbox(self.access_token)

    def run(self):
        self.active_download_threads += 1
        # Fetch metadata of the video from Dropbox
        metadata = self.dbx.files_get_metadata(self.dropbox_path)
        file_size = metadata.size

        # Initialize tqdm progress bar for downloading
        progress = tqdm(total=file_size, unit='B', unit_scale=True,
                        desc=f"Downloading {self.dropbox_path}=>{self.download_path}")

        # Fetch the video from Dropbox
        _, response = self.dbx.files_download(self.dropbox_path)

        # Save the video to a temporary file and update the progress bar
        temp_filename = f"{self.download_path}.{self.download_sufix}"
        with open(temp_filename, 'wb') as temp_file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                progress.update(len(chunk))
                temp_file.write(chunk)
        progress.close()
        print(f"Remove the temporary Dropbox file after processing {self.download_path}")
        shutil.move(temp_filename, self.download_path)
        self.active_download_threads -= 1

@dataclass
class DropboxDownloaderConfig:
    access_token: str
    dropbox_folder: str
    file_mask: str
    num_threads: int
    start_delay: int
    download_folder: str
    download_suffix: str = "downloading"
class DropboxDownloader:
    def __init__(self, c:DropboxDownloaderConfig):
        self.dbx = dropbox.Dropbox(c.access_token)
        self.access_token = c.access_token
        self.dropbox_folder = c.dropbox_folder
        self.file_mask = c.file_mask
        self.num_threads = c.num_threads
        self.start_delay = c.start_delay
        self.download_folder = c.download_folder
        self.download_suffix = c.download_suffix


    def download(self):
        files_to_download = self.list_dropbox_files()
        threads = []

        for dropbox_path in files_to_download:
            output_path = self.make_output_path(dropbox_path)
            _, file_extension = os.path.splitext(self.file_mask)
            thread = DropboxDownload(self.access_token, dropbox_path, output_path, self.download_suffix)
            threads.append(thread)
            thread.start()
            time.sleep(self.start_delay)

            while DropboxDownload.active_download_threads >= self.num_threads:
                time.sleep(1)

    def list_dropbox_files(self):
        # Convert file_mask (wildcard pattern) to regex pattern
        pattern = re.compile(self.file_mask.replace('.', r'\.').replace('*', '.*') + '$')

        results = []

        # Initialize with the first call
        result = self.dbx.files_list_folder(self.dropbox_folder, recursive=True)

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

    def make_output_path(self, file_path):
        rel_path = os.path.relpath(file_path, self.dropbox_folder)
        output_path = os.path.join(self.download_folder, rel_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        return output_path

if __name__ == "__main__":
    access_token = input("Access token:")
    c = DropboxDownloaderConfig(
        access_token=access_token,
        dropbox_folder="/andriyaka/",
        download_folder="D:\\docs\dest\\1p1media\soft\\videobase\\tests\\video_test\\dropbox\\downloaded\\",
        file_mask="*.ts",
        num_threads=2,
        start_delay=1
    )
    DropboxDownloader(c).download()

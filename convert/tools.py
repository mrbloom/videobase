import os
import dropbox
import subprocess
from tqdm import tqdm
from threading import Thread
from queue import Queue
import shutil
import time
import platform
import psutil


MAX_RETRIES = 3
RETRY_WAIT = 10  # wait 10 seconds before retrying


def convert(ffmpeg_path, dropbox_input_folder, local_output_folder, access_token):
    START_FOLDER = dropbox_input_folder

    # Initialize Dropbox client
    ACCESS_TOKEN = access_token

    # def refresh_token():
    #     print("GOTO http://dropbox.com/developers/apps")
    #     global ACCESS_TOKEN
    #     ACCESS_TOKEN = input("ACCESS_TOKEN=")
    #     print(f"Hard coded ACCESS_TOKEN={ACCESS_TOKEN}")

    def convert_file(local_path, converted_path):
        cmd = [
            os.path.join(ffmpeg_path, "ffmpeg"),
            "-hwaccel", "cuda", "-hwaccel_output_format", "cuda",
            '-i', local_path,
            '-c:v', 'h264_nvenc', '-c:a', 'copy', '-b:v', '1.5M', '-y',
            converted_path
        ]
        print(f"Converting {local_path} to {converted_path}")
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        os.remove(local_path)

    def convert_downloaded_files(downloaded_files_queue):
        while True:
            file_to_convert = downloaded_files_queue.get()
            if file_to_convert is None:  # A sentinel to stop the loop.
                break
            local_path, converted_path = file_to_convert
            convert_file(local_path, converted_path)
            downloaded_files_queue.task_done()

    def timed_download(dropbox_path, local_path):
        """Download a file from Dropbox and track progress, with retrying."""
        retries = 0
        while retries < MAX_RETRIES:
            try:
                try:
                    metadata, res = dbx.files_download(dropbox_path)
                except dropbox.exceptions.AuthError:
                    print("Token expired, refreshing...")
                    return
                    # refresh_token()
                    # metadata, res = dbx.files_download(dropbox_path)
                except Exception as e:
                    print(f"An error occurred: {e}")
                # work only with 2023 folders
                parent_folder = os.path.dirname(local_path)
                last_subfolder = os.path.basename(parent_folder)

                if last_subfolder.startswith("2023"):
                    print("The last subfolder starts with 2023!")
                else:
                    print("The last subfolder does not start with 2023.")
                    return

                # Determine converted filename
                base_name = os.path.basename(local_path)
                if base_name.startswith("02"):
                    base_name = "2Russia24" + base_name[2:]
                    output_dir = os.path.join(os.path.dirname(local_path), "2Russia24")
                elif base_name.startswith("03"):
                    base_name = "3PlanetaRTR" + base_name[2:]
                    output_dir = os.path.join(os.path.dirname(local_path), "3PlanetaRTR")
                else:
                    output_dir = os.path.dirname(local_path)

                os.makedirs(output_dir, exist_ok=True)
                converted_path = os.path.join(output_dir, base_name + ".mp4")

                # Check if the converted file already exists
                if os.path.exists(converted_path):
                    print(f"Converted file {converted_path} already exists. Skipping download.")
                    return

                with open(local_path, 'wb') as local_file:
                    for chunk in tqdm(res.iter_content(chunk_size=1024), total=int(metadata.size / 1024), unit="MB"):
                        local_file.write(chunk)

                downloaded_files_queue.put((local_path, converted_path))

                # if successful, break out of the retry loop
                break

            except (dropbox.exceptions.HttpError, ConnectionError) as e:
                if retries < MAX_RETRIES - 1:  # don't print this on the last retry
                    print(f"Error downloading {dropbox_path}. Retrying in {RETRY_WAIT} seconds...")
                    time.sleep(RETRY_WAIT)
                retries += 1
            else:
                print(f"Failed to download {dropbox_path} after {MAX_RETRIES} attempts.")

    def download_file(dropbox_path, local_path, retries=MAX_RETRIES):
        while retries > 0:
            download_thread = Thread(target=timed_download, args=(dropbox_path, local_path))
            download_thread.start()

            # Wait for the thread to finish or until timeout
            download_thread.join(timeout=15 * 60)  # 15 minutes in seconds

            # Check if the thread is still alive (timed out)
            if download_thread.is_alive():
                print(f"Warning: Downloading {dropbox_path} took longer than 15 minutes!")
                if os.path.exists(local_path):
                    os.remove(local_path)  # Remove the partially downloaded file
                retries -= 1
                if retries > 0:
                    print(f"Retrying download for {dropbox_path}. Remaining retries: {retries}")
            else:
                # The file download was successful, break the loop
                break

    def download_folder(dropbox_path, local_path):
        """Download the contents of a Dropbox folder to a local folder"""
        try:
            folder_metadata = dbx.files_list_folder(dropbox_path).entries
            os.makedirs(local_path, exist_ok=True)

            for item in folder_metadata:
                if isinstance(item, dropbox.files.FileMetadata):
                    if item.name.startswith(("02", "03")):
                        print(f"{item.path_lower} => {os.path.join(local_path, item.name)}")
                        download_file(item.path_lower, os.path.join(local_path, item.name))
                elif isinstance(item, dropbox.files.FolderMetadata):
                    download_folder(item.path_lower, os.path.join(local_path, item.name))
                else:
                    print(f"Skipping {item.path_lower}")

        except dropbox.exceptions.ApiError as e:
            if isinstance(e.error, dropbox.files.ListFolderError) and \
                    isinstance(e.error.get_path(), dropbox.files.LookupError) and \
                    e.error.get_path().is_not_found():
                print(f"Error: The specified folder {dropbox_path} does not exist on Dropbox.")
            else:
                print(f"Error downloading folder {dropbox_path} to {local_path}: {e}")
        except Exception as e:
            print(f"Error downloading folder {dropbox_path} to {local_path}: {e}")

    # Start the conversion thread
    downloaded_files_queue = Queue()
    conversion_thread = Thread(target=lambda: convert_downloaded_files(downloaded_files_queue))
    conversion_thread.start()

    # refresh_token()

    start_folder = START_FOLDER

    dbx = dropbox.Dropbox(ACCESS_TOKEN)

    dbx = dropbox.Dropbox(ACCESS_TOKEN)

    try:
        entries = dbx.files_list_folder(START_FOLDER).entries
    except dropbox.exceptions.ApiError as e:
        if isinstance(e.error, dropbox.files.ListFolderError) and \
                isinstance(e.error.get_path(), dropbox.files.LookupError) and \
                e.error.get_path().is_not_found():
            print(f"Error: The specified folder {START_FOLDER} does not exist on Dropbox.")
            exit()
        else:
            print(f"Error listing folder contents for {START_FOLDER}: {e}")
            exit()

    for entry in entries:
        print(f"Download {START_FOLDER}/{entry.name}")
        download_folder(f"{START_FOLDER}/{entry.name}", os.path.join(local_output_folder, entry.name))

    # Once everything is done, put a sentinel value to stop the conversion loop
    downloaded_files_queue.put(None)
    conversion_thread.join()

# End of function



def convert_videos_quick_sync(input_directory, output_directory,n_threads=5,sleep_sek=240, VIDEO_EXT = ".ts",OUTPUT_EXT = ".mp4"):


    REQUIRED_SPACE_GB = 1*n_threads  # in GB

    """
    Convert videos from the specified directory and its subdirectories.

    :param input_directory: The root directory to start looking for video files.
    """
    for root, _, files in os.walk(input_directory):
        for file in files:
            if file.endswith(VIDEO_EXT):
                full_path = os.path.join(root, file)
                filename, _ = os.path.splitext(file)

                foldername = set_folder_name(filename[:2])
                if not foldername:
                    continue

                folder_path = os.path.join(output_directory, foldername)
                if not os.path.exists(folder_path):
                    os.mkdir(folder_path)

                output_temp = os.path.join(root, f"{foldername}_{filename}_SD_1.5Mbit{OUTPUT_EXT}")
                output_final = os.path.join(folder_path, f"{foldername}_{filename}_SD_1.5Mbit{OUTPUT_EXT}")

                # Only proceed if the output doesn't already exist
                if not os.path.exists(output_final) and not os.path.exists(output_temp):
                    if check_diskspace(root) < REQUIRED_SPACE_GB:
                        print(f"Not enough space on the disk at {root}. Required: {REQUIRED_SPACE_GB}GB.")
                        continue

                    # Execute ffmpeg n_threads command with delay
                    for _ in range(n_threads):
                        # subprocess.run(["start","./ffmpeg", "-hwaccel", "qsv", "-c:v", "mpeg2_qsv", "-i", full_path,
                        #             "-c:v", "h264_qsv", "-b:v", "1.5M", "-y", output_temp])
                        subprocess.run(["start","./ffmpeg", "-i", full_path,
                                    "-c:v", "h264", "-b:v", "1.5M", "-y", output_temp])
                        time.sleep(sleep_sek)
                    # Move the temp file to final location if its size is acceptable (greater than 10000 bytes)
                    if os.path.getsize(output_temp) > 10000:
                        shutil.move(output_temp, output_final)


def set_folder_name(prefix):
    """Determine the target folder name based on the prefix."""
    folder_map = {
        "02": "2Russia24",
        "03": "3PlanetaRTR"
    }
    return folder_map.get(prefix, "")


def check_diskspace(folder_path="."):
    BYTES_IN_GB = 10 ** 9  # Bytes per GB

    if platform.system() == "Windows":
        free_space_bytes = psutil.disk_usage(folder_path).free
    else:
        st = os.statvfs(folder_path)
        free_space_bytes = st.f_bavail * st.f_frsize

    free_space_gb = free_space_bytes / BYTES_IN_GB
    return free_space_gb




import os
import subprocess
import dropbox


def convert(ffmpeg_path, dropbox_input_folder, local_output_folder, access_token):
    MAX_RETRIES = 3
    RETRY_WAIT = 10  # wait 10 seconds before retrying
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
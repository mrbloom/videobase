import os
import threading
import shutil
import time
import platform
import psutil
import ffmpeg

counter = 0

def convert_videos_quick_sync(ffmpeg_folder, input_directory, output_directory, n_threads, delay_sec, VIDEO_EXT=".ts",
                              OUTPUT_EXT=".mp4"):
    threads = []

    for i in range(n_threads):
        thread = threading.Thread(target=convert_video_quick_sync,
                                  args=(
                                      ffmpeg_folder, n_threads, input_directory, output_directory, VIDEO_EXT,
                                      OUTPUT_EXT))
        threads.append(thread)
        thread.start()
        time.sleep(delay_sec)

    for thread in threads:
        thread.join()


def convert_video_quick_sync(ffmpeg_folder, n_threads, input_directory, output_directory, VIDEO_EXT, OUTPUT_EXT):
    REQUIRED_SPACE_GB = 1 * n_threads  # in GB
    # Set the path to ffmpeg executable
    os.environ['PATH'] += os.pathsep + ffmpeg_folder

    for root, _, files in os.walk(input_directory):
        for file in files:
            if file.endswith(VIDEO_EXT):
                full_path = os.path.join(root, file)
                input_subfolder = root.replace(input_directory + "\\", "")
                filename, _ = os.path.splitext(file)

                foldername = set_folder_name(filename[:2])
                if not foldername:
                    continue

                folder_path = os.path.join(output_directory, input_subfolder, foldername)
                if not os.path.exists(folder_path):
                    try:
                        os.makedirs(folder_path)
                    except OSError as error:
                        print(error)

                output_temp = os.path.join(root, f"{foldername}_{filename}_SD_1.5Mbit{OUTPUT_EXT}")
                output_final = os.path.join(folder_path, f"{foldername}_{filename}_SD_1.5Mbit{OUTPUT_EXT}")

                if not os.path.exists(output_temp) and not os.path.exists(output_final):
                    ffmpeg_convert_quicksync(root,REQUIRED_SPACE_GB,full_path,output_temp,output_final)


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


def ffmpeg_convert_quicksync(root,REQUIRED_SPACE_GB,full_path,output_temp,output_final):
    global counter
    counter = counter + 1
    print(f"WTF = {counter}")
    if check_diskspace(root) < REQUIRED_SPACE_GB:
        print(f"Not enough space on the disk at {root}. Required: {REQUIRED_SPACE_GB}GB.")
        return

    with open(output_temp, "w") as dumb_file:
        dumb_file.write("dumb file")
    try:
        (
            ffmpeg
            .input(full_path)
            .output(output_temp,
                    vcodec="h264",
                    video_bitrate="1.5M")
            .overwrite_output()
            .run_async()
        )
        # cmd_str = ' '.join(
        #     ffmpeg
        #     .input(full_path)
        #     .output(output_temp,
        #             vcodec="h264",
        #             video_bitrate="1.5M")
        #     .overwrite_output()
        #     .compile()
        # )
        # # Use subprocess to run the command in a new window
        # print(f"Run:{cmd_str}")
        # subprocess.run(f'start cmd /k "{cmd_str}"', shell=True)
    except ffmpeg.Error as e:
        print(f"Error converting {full_path} to {output_temp}: {e.stderr.decode()}")

        # Move the temp file to final location if its size is acceptable (greater than 10000 bytes)
    if os.path.getsize(output_temp) > 10000:
        shutil.move(output_temp, output_final)

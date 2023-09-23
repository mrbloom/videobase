import os
from flask import Blueprint, render_template, request

from .tools import dropboxvideo,localvideo


N_MAX_THREADS = 32

convert = Blueprint('convert', __name__, template_folder='templates', static_folder='static')

@convert.route('/', methods=["POST", "GET"])
def index():
    if request.method == "POST":
        ffmpeg_folder = request.form['ffmpeg_folder']
        output_folder = request.form['output_folder']
        dropbox_folder = request.form['dropbox_folder']
        access_token = request.form['access_token']
        input_folder = request.form['input_folder']
        n_threads = int(request.form['n_threads'])
        delay_sec = int(request.form['delay_sec'])
        file_mask = request.form['file_mask']
        video_codec = request.form['video_codec']
        video_bitrate = request.form['video_bitrate']
        output_ext = request.form['output_ext']


        print("FFmpeg folder:", ffmpeg_folder)
        print("Input folder:", input_folder)
        print("Output folder:", output_folder)
        print("Dropbox folder:",dropbox_folder)
        print("ACCESS_TOKEN:", access_token)

        if dropbox_folder and access_token:
            config = dropboxvideo.ConfigFFMPEGDropboxConverter(
                dropbox_input=dropbox_folder,
                dropbox_output="",
                access_token=access_token,
                ffmpeg_path=ffmpeg_folder,
                num_threads=n_threads,
                start_delay=delay_sec,
                input_folder=input_folder,
                output_folder=output_folder,
                file_mask=file_mask,
                video_codec=video_codec,
                video_bitrate=video_bitrate,
                output_ext=output_ext
            )
            convertor = dropboxvideo.FFMPEGDropboxConverter(config)
            convertor.convert()
        if input_folder and output_folder:

            config=localvideo.ConfigFFMPEGConverter(
                ffmpeg_path=ffmpeg_folder,
                num_threads=n_threads,
                start_delay=delay_sec,
                input_folder=input_folder,
                output_folder=output_folder,
                file_mask=file_mask,
                video_codec=video_codec,
                video_bitrate=video_bitrate,
                output_ext=output_ext
            )

            convertor = localvideo.FFMPEGConverter(config)
            convertor.convert()

    return render_template('convert/index.html', n_threads=N_MAX_THREADS)

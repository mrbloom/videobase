import os
from flask import Blueprint, render_template, request

from .tools import drpbx, video


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


        print("FFmpeg folder:", ffmpeg_folder)
        print("Input folder:", input_folder)
        print("Output folder:", output_folder)
        print("Dropbox folder:",dropbox_folder)
        print("ACCESS_TOKEN:", access_token)

        if not input_folder and dropbox_folder and access_token:
            drpbx.convert(ffmpeg_folder, dropbox_folder, output_folder, access_token)
        if not access_token and not dropbox_folder and input_folder:
            convertor = video.FFMPEGConverter(ffmpeg_folder, n_threads, delay_sec, input_folder,output_folder, "02*.ts")
            convertor.convert()

    return render_template('convert/index.html', n_threads=N_MAX_THREADS)

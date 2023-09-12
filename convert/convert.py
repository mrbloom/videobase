import os
from flask import Blueprint, render_template, request
from . import tools

convert = Blueprint('convert', __name__, template_folder='templates', static_folder='static')

@convert.route('/', methods=["POST", "GET"])
def index():
    if request.method == "POST":
        ffmpeg_folder = request.form['ffmpeg_folder']
        output_folder = request.form['output_folder']
        dropbox_folder = request.form['dropbox_folder']
        access_token = request.form['access_token']
        input_folder = request.form['input_folder']


        print("FFmpeg folder:", ffmpeg_folder)
        print("Input folder:", input_folder)
        print("Output folder:", output_folder)
        print("Dropbox folder:",dropbox_folder)
        print("ACCESS_TOKEN:", access_token)

        if not input_folder and dropbox_folder and access_token:
            tools.convert(ffmpeg_folder, dropbox_folder, output_folder, access_token)
        if not access_token and not dropbox_folder and input_folder:
            tools.convert_videos_quick_sync(input_folder,output_folder)


    return render_template('convert/index.html')

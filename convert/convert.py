import os
from flask import Blueprint, render_template, request
from . import tools

convert = Blueprint('convert', __name__, template_folder='templates', static_folder='static')

@convert.route('/', methods=["POST", "GET"])
def index():
    if request.method == "POST":
        ffmpeg_path = request.form['derived_ffmpeg_path']
        video_path = request.form['derived_video_path']
        dropbox_video_path = request.form['dropbox_video_path']
        access_token = request.form['access_token']
        input_folder = request.form['derived_input_path']


        print("Derived FFmpeg Path:", ffmpeg_path)
        print("Derived Video Root Path:", video_path)
        print("ACCESS_TOKEN:", access_token)

        if dropbox_video_path and access_token:
            tools.convert(ffmpeg_path, dropbox_video_path, video_path, access_token)
        if not access_token and input_folder:
            tools.convert_videos_quick_sync(input_folder,video_path)


    return render_template('convert/index.html')

from flask import Blueprint, render_template, send_from_directory, current_app, request, redirect, url_for
import os

explorer = Blueprint('explorer', __name__, template_folder='templates', static_folder='static')


def get_files_recursive(folder):
    """Return all video files from folder and its subfolders."""
    videos = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(('.mp4', '.webm')):
                relative_path = os.path.relpath(os.path.join(root, file), folder)
                videos.append(relative_path)
    return videos


@explorer.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        folder = request.form.get('root_folder')
        if os.path.exists(folder):
            current_app.config['VIDEOS_FOLDER'] = folder

    videos_folder = current_app.config.get('VIDEOS_FOLDER', os.path.join(current_app.root_path, 'static', 'videos'))
    videos = get_files_recursive(videos_folder)
    return render_template('explorer/index.html', videos=videos)


@explorer.route('/play/<path:video_path>')
def play_video(video_path):
    videos_folder = current_app.config.get('VIDEOS_FOLDER', os.path.join(current_app.root_path, 'static', 'videos'))
    video_path_full = os.path.join(videos_folder, video_path)
    if os.path.exists(video_path_full):
        return render_template('explorer/play.html', video_path=video_path)
    return "Video not found", 404

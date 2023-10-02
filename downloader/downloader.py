from flask import Blueprint, render_template, request

from .tools.downloadvideo import DropboxDownloaderConfig, DropboxDownloader

downloader = Blueprint('downloader', __name__, template_folder='templates', static_folder='static')

N_MAX_THREADS = 32


@downloader.route('/', methods=["POST", "GET"])
def index():
    if request.method == "POST":
        dropbox_folder = request.form['dropbox_folder']
        access_token = request.form['access_token']
        input_folder = request.form['input_folder']
        n_threads = int(request.form['n_threads'])
        delay_sec = int(request.form['delay_sec'])
        file_mask = request.form['file_mask']

        print("Input folder:", input_folder)
        print("Dropbox folder:", dropbox_folder)
        print("ACCESS_TOKEN:", access_token)

        if dropbox_folder and access_token and input_folder:
            c = DropboxDownloaderConfig(
                access_token=access_token,
                dropbox_folder=dropbox_folder,
                download_folder=input_folder,
                file_mask=file_mask,
                num_threads=n_threads,
                start_delay=delay_sec
            )
            DropboxDownloader(c).download()

    return render_template('downloader/index.html', n_threads=N_MAX_THREADS)
    # return "downloader"
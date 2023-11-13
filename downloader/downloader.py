from flask import Blueprint, render_template, request

from .tools.downloadvideo import DropboxDownloaderConfig, DropboxDownloader
from .forms import DownloadForm

downloader = Blueprint('downloader', __name__, template_folder='templates', static_folder='static')

N_MAX_THREADS = 32


@downloader.route('/', methods=["POST", "GET"])
def index():
    if request.method == "POST":
        form = DownloadForm()
        if form.validate_on_submit():
            dropbox_folder = form.dropbox_folder.data
            access_token = form.access_token.data
            input_folder = form.input_folder.data
            n_threads = int(form.n_threads.data)
            delay_sec = form.delay_sec.data
            file_mask = form.file_mask.data

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

    return render_template('downloader/index.html', n_threads=N_MAX_THREADS, form=form)
    # return "downloader"
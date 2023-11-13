from flask import Blueprint, render_template, request, flash, current_app
# from flask_socketio import emit
# from . import socketio  # Import the socketio instance
from wtforms import Form, StringField, IntegerField, SelectField, BooleanField, validators, SubmitField
from .tools import localvideo

N_MAX_THREADS = 32

convert = Blueprint('convert', __name__, template_folder='templates', static_folder='static')


class VideoConversionForm(Form):
    ffmpeg_folder = StringField('Select FFMPEG bin', default="")
    n_threads = SelectField('Select number of FFMPEGs', choices=[(i, i) for i in range(1, N_MAX_THREADS)])
    delay_sec = IntegerField('Select deley between FFMPEGs in seconds', default=1,
                             validators=[validators.NumberRange(min=0)])
    input_keys_str = StringField('Place input keys', default="")
    output_keys_str = StringField('Place output keys', default="")
    input_folder = StringField('Input folder', [validators.InputRequired()])
    input_file_mask = StringField('Input file mask', [validators.InputRequired()])
    video_codec = StringField('Video Codec', default="h264")
    video_bitrate = StringField('Video Bitrate', default="1.5M")
    output_folder = StringField('Output folder', [validators.InputRequired()])
    output_file_mask = StringField('Output file mask', [validators.InputRequired()])
    overwrite_files = BooleanField('Overwrite')
    overwrite_if_duration = BooleanField('Check duration. Overwrite', default=True)

    submit = SubmitField('Submit')


@convert.route('/', methods=["POST", "GET"])
def index():
    form = VideoConversionForm(request.form)
    if request.method == "POST" and form.validate():
        ffmpeg_folder = form.ffmpeg_folder.data
        output_folder = form.output_folder.data
        input_folder = form.input_folder.data
        n_threads = int(form.n_threads.data)
        delay_sec = form.delay_sec.data
        input_file_mask = form.input_file_mask.data
        video_codec = form.video_codec.data
        video_bitrate = form.video_bitrate.data
        output_file_mask = form.output_file_mask.data
        input_keys_str = form.input_keys_str.data
        output_keys_str = form.output_keys_str.data
        overwrite_files = form.overwrite_files.data
        overwrite_if_duration = form.overwrite_if_duration.data
        print(f"0verwrite if duration = {overwrite_if_duration}")

        print("FFmpeg folder:", ffmpeg_folder)
        print("Input folder:", input_folder)
        print("Output folder:", output_folder)

        if input_folder and output_folder:
            config = localvideo.ConfigFFMPEGConverter(
                ffmpeg_path=ffmpeg_folder,
                num_threads=n_threads,
                start_delay=delay_sec,
                input_folder=input_folder,
                output_folder=output_folder,
                input_file_mask=input_file_mask,
                video_codec=video_codec,
                video_bitrate=video_bitrate,
                output_file_mask=output_file_mask,
                input_keys_str=input_keys_str,
                output_keys_str=output_keys_str,
                overwrite_files=overwrite_files,
                overwrite_if_duration=overwrite_if_duration
            )
            convertor = localvideo.FFMPEGConverter(config)
            files_to_convert = convertor.get_files()
            unconverted_files = convertor.get_unconverted_files(files_to_convert)
            percent_unready = round(len(unconverted_files)/len(files_to_convert), 2)
            # print(f"Files to convert {files_to_convert}")
            print(f"We have {100-percent_unready}% converted files.")
            print(f"The number of unconverted is {len(unconverted_files)}")
            print(f"The number of all files is {len(files_to_convert)}")
            if len(unconverted_files)>10:
                print(unconverted_files[:5]," ... ",unconverted_files[-5:])
            else:
                print(unconverted_files)
            convertor.convert(files_to_convert)
        elif request.method == "POST" and not form.validate():
            flash('Please correct the errors in the form')

    return render_template('convert/index.html', form=form, n_threads=N_MAX_THREADS)

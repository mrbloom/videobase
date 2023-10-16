from flask import Blueprint, render_template, request, flash
from wtforms import Form, StringField, IntegerField, SelectField, BooleanField, validators, SubmitField
from .tools import localvideo


N_MAX_THREADS = 32

convert = Blueprint('convert', __name__, template_folder='templates', static_folder='static')


class VideoConversionForm(Form):
    ffmpeg_folder = StringField('Select FFMPEG bin', default="")
    n_threads = SelectField('Select number of FFMPEGs', choices=[(i, i) for i in range(1, N_MAX_THREADS)])
    delay_sec = IntegerField('Select deley between FFMPEGs in seconds', default=1, validators=[validators.NumberRange(min=0)])
    input_keys_str = StringField('Place input keys',default="")
    output_keys_str = StringField('Place output keys',default="")
    input_folder = StringField('Input folder', [validators.InputRequired()])
    input_file_mask = StringField('Input file mask', [validators.InputRequired()])
    video_codec = StringField('Video Codec', default="h264")
    video_bitrate = StringField('Video Bitrate', default="1.5M")
    output_folder = StringField('Output folder', [validators.InputRequired()])
    output_file_mask = StringField('Output file mask', [validators.InputRequired()])
    overwrite_files = BooleanField('Overwrite')

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


        print("FFmpeg folder:", ffmpeg_folder)
        print("Input folder:", input_folder)
        print("Output folder:", output_folder)


        if input_folder and output_folder:

            config=localvideo.ConfigFFMPEGConverter(
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
                overwrite_files = overwrite_files
            )
            convertor = localvideo.FFMPEGConverter(config)
            convertor.convert()
        elif request.method == "POST" and not form.validate():
            flash('Please correct the errors in the form')

    return render_template('convert/index.html', form=form, n_threads=N_MAX_THREADS)

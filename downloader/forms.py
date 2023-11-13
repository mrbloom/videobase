from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField
from wtforms.validators import DataRequired, NumberRange

class DownloadForm(FlaskForm):
    dropbox_folder = StringField('Dropbox Folder', validators=[DataRequired()])
    access_token = StringField('Access Token', validators=[DataRequired()])
    input_folder = StringField('Input Folder', validators=[DataRequired()])
    n_threads = SelectField('Number of Download Streams', choices=[(str(i), i) for i in range(1, 33)], validators=[DataRequired()])
    delay_sec = IntegerField('Delay Between Downloads (Seconds)', validators=[DataRequired(), NumberRange(min=0)])
    file_mask = StringField('File Mask', validators=[DataRequired()], default='*.ts')

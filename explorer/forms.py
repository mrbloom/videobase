from wtforms import StringField, validators, Form, SubmitField


class VideosConvertedForm(Form):
    input_folder = StringField('Input folder', [validators.InputRequired()])
    input_file_mask = StringField('Input file mask', [validators.InputRequired()])
    output_folder = StringField('Output folder', [validators.InputRequired()])
    output_file_mask = StringField('Output file mask', [validators.InputRequired()])


    submit = SubmitField('Submit')
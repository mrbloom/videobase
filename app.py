from flask import Flask, render_template
from convert.convert import convert

app = Flask(__name__)
app.secret_key = 'some_secret_key_for_flask_messages'

# Register the video conversion blueprint
app.register_blueprint(convert, url_prefix='/convert')


@app.route('/')
def homepage():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

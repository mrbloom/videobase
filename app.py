from flask import Flask, render_template
from convert.convert import convert
from downloader.downloader import downloader

app = Flask(__name__)
app.secret_key = 'some_secret_key_for_flask_messages'

# Register the blueprints
app.register_blueprint(convert, url_prefix='/convert')
app.register_blueprint(downloader, url_prefix='/downloader')


@app.route('/')
def homepage():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, render_template

from convert.convert import convert
from downloader.downloader import downloader
from explorer.explorer import explorer

from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Register the blueprints
app.register_blueprint(convert, url_prefix='/convert')
app.register_blueprint(downloader, url_prefix='/downloader')
app.register_blueprint(explorer, url_prefix='/explorer')


@app.route('/')
def homepage():
    return render_template('index.html')


if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True )
    # app.run(debug=True)

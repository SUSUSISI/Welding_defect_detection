from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)


@socketio.on('connect')
def connect():

    emit('message', {'hello': "Hello"})


@app.route('/')
def index():
    print("dddd")
    return render_template('wanni.html')


if __name__ == '__main__':
       socketio.run(app, debug=True)
import socketio
import socketio.exceptions as sioe
import threads
import time

sio = socketio.Client()


class ServerConnectionThread(threads.CustomThread):
    def __init__(self, address, port):
        self.address = address
        self.port = port
        super().__init__()

    def kill(self):
        super().kill()
        sio.disconnect()

    def run(self):
        while not self.FLAG_KILL:
            if sio.connected is False:
                time.sleep(1)
                try:
                    connect_server(self.address, self.port)
                except sioe.SocketIOError:
                    print("Server Connection Error")
            elif sio.connected is True:
                time.sleep(1)

            while self.FLAG_PAUSE:
                time.sleep(0.1)


def base_connection_callback_func(flag):
    if flag is True:
        print("서버와 연결이 되었습니다.")
    elif flag is False:
        print("서버와 연결이 해제되었습니다.")
    elif flag is None:
        print("서버와 연결이 되지 않습니다.")


def base_data_request_callback_func(flag, speed):
    print("-----------------------")
    print("Server Request Data")
    print("Flag : ", flag)
    print("speed: ", speed)
    print("-----------------------")


connection_callback_func = base_connection_callback_func
data_request_callback_func = base_data_request_callback_func


@sio.event
def connect_error(error):
    connection_callback_func(None)


@sio.event(namespace='/node')
def connect():
    connection_callback_func(True)


@sio.event(namespace='/node')
def disconnect():
    connection_callback_func(False)


@sio.event(namespace='/node')
def data_request(data):
    data_request_callback_func(data['request'], data['speed'])


def kill():
    sio.disconnect()


def connect_server(address, port):
    sio.connect('http://' + address +
                ":" + port, namespaces=['/node'])


def send_current_status(flag, data):
    print("send current status ")
    sio.emit('current_status', {'status': flag, 'data': {'current': data[0],
                                                         'voltage': data[1],
                                                         'wire_feed': data[2]}}, namespace='/node')


def send_data_set(pid, file_path):
    print("send data set")
    print("pid : ", pid)
    with open(file_path, 'rb') as f:
        data = f.read()
        sio.emit('data_set', {'data': data, 'process_id': pid}, namespace='/node')

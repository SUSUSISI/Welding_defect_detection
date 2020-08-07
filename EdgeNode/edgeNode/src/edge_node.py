from pymodbus.client.sync import ModbusTcpClient
import time
import threads
import FaDAm as fd
from datetime import datetime
import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import QTextCursor
import socketio
from threading import Thread
import server

form_class = uic.loadUiType("ui/edgenode.ui")[0]


class EdgeNode(QMainWindow, form_class):

    PID = 1
    data_set = None
    current_time = None
    current_data = None
    done_data_set = None
    path = "data/started_" + datetime.now().strftime('%Y_%m_%d_%H%M%S') + "/"

    plc_address = '172.30.1.20'
    plc_port = '5020'
    plc_client = None

    server_address = '123.123.123.123'
    server_port = '5020'

    FLAG_WELDING = False
    __FLAG_PLC_CONNECTION = False
    __FLAG_SERVER_CONNECTION = False
    __FLAG_SERVER_DATA_REQUEST = False

    __server_connection_thread = None
    __read_plc_thread = None
    __send_data_set_thread = None
    __send_current_status_thread = None

    def __init__(self):
        super().__init__()
        server.connection_callback_func = self.server_connection_callback_func
        server.data_request_callback_func = self.server_data_request_callback_func
        self.init_ui()

    def server_connection_callback_func(self, flag):
        if flag is True:
            self.set_FLAG_SERVER_CONNECTION(True)
            self.log_server("서버에 연결되었습니다.")
        elif flag is False:
            self.set_FLAG_SERVER_CONNECTION(False)
            self.log_server("서버와 연결이 해제되었습니다.")
        elif flag is None:
            self.set_FLAG_SERVER_CONNECTION(False)
            self.log_server("서버와 연결이 되지 않습니다.")

    def server_data_request_callback_func(self, flag, speed):
        self.set_FLAG_SERVER_DATA_REQUEST(flag)
        if self.__send_current_status_thread is not None:
            self.__send_current_status_thread.clock_time = speed
        if flag is False:
            self.lb_server_data_speed.setText('')
        else:
            self.lb_server_data_speed.setText(str(speed) + ' s')

    def send_current_status(self):
        if self.__FLAG_SERVER_CONNECTION and self.__FLAG_SERVER_DATA_REQUEST:
            print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S.%f]: '), "Send Current Data")
            server.send_current_status(self.FLAG_WELDING, self.current_data)

    def send_data_set(self, pid, file_path):
        if self.__FLAG_SERVER_CONNECTION and self.__FLAG_SERVER_DATA_REQUEST:
            self.log_server('파일 전송 (' + file_path + ')')
            server.send_data_set(pid, file_path)
        else:
            self.log_server('파일 전송 안함 (' + file_path + ')')

    def log_plc(self, msg):
        when = datetime.now().strftime('[%Y_%m_%d %H:%M:%S]: ')
        self.tb_log_plc.append(when + msg)
        self.tb_log_plc.moveCursor(QTextCursor.End)

    def log_server(self, msg):
        when = datetime.now().strftime('[%Y_%m_%d %H:%M:%S]: ')
        self.tb_log_server.append(when + msg)
        self.tb_log_server.moveCursor(QTextCursor.End)

    def set_FLAG_WELDING(self, flag):
        self.FLAG_WELDING = flag
        if flag:
            self.lb_plc_welding.setStyleSheet('image:url(ui/green.png);')
        else:
            self.lb_plc_welding.setStyleSheet('image:url(ui/red.png);')

    def set_FLAG_SERVER_DATA_REQUEST(self, flag):
        self.__FLAG_SERVER_DATA_REQUEST = flag
        if flag:
            self.lb_server_data_reqeust.setStyleSheet('image:url(ui/green.png);')
        else:
            self.lb_server_data_request.setStyleSheet('image:url(ui/red.png);')

    def set_FLAG_PLC_CONNECTION(self, flag):
        self.__FLAG_PLC_CONNECTION = flag
        if flag:
            self.lb_plc_status.setStyleSheet('image:url(ui/green.png);')
        else:
            self.lb_plc_status.setStyleSheet('image:url(ui/red.png);')

    def get_FLAG_SERVER_CONNECTION(self):
        return self.__FLAG_SERVER_CONNECTION

    def set_FLAG_SERVER_CONNECTION(self, flag):
        self.__FLAG_SERVER_CONNECTION = flag
        if flag:
            self.lb_server_status.setStyleSheet('image:url(ui/green.png);')
        else:
            self.lb_server_status.setStyleSheet('image:url(ui/red.png);')

    def init_ui(self):
        self.setupUi(self)

        self.le_server_address.setText(self.server_address)
        self.le_server_port.setText(self.server_port)
        self.le_plc_address.setText(self.plc_address)
        self.le_plc_port.setText(self.plc_port)
        self.lb_server_status.setStyleSheet('image:url(ui/red.png);')
        self.lb_plc_status.setStyleSheet('image:url(ui/red.png);')
        self.lb_server_data_request.setStyleSheet('image:url(ui/red.png);')
        self.lb_plc_welding.setStyleSheet('image:url(ui/red.png);')

        self.btn_stop.setEnabled(False)
        self.btn_run.clicked.connect(self.btn_run_func)
        self.btn_stop.clicked.connect(self.btn_stop_func)

    def btn_run_func(self):
        self.btn_run.setEnabled(False)
        self.le_server_address.setEnabled(False)
        self.le_server_port.setEnabled(False)
        self.le_plc_address.setEnabled(False)
        self.le_plc_port.setEnabled(False)
        self.btn_stop.setEnabled(True)

        self.server_address = self.le_server_address.text()
        self.server_port = self.le_server_port.text()
        self.plc_address = self.le_plc_address.text()
        self.plc_port = self.le_plc_port.text()
        self.run()

    def wait_stop(self):
        while self.__read_plc_thread.is_alive() or self.__server_connection_thread.is_alive() \
                or self.__send_data_set_thread.is_alive() or self.__send_current_status_thread.is_alive():
            time.sleep(0.5)

        self.btn_run.setEnabled(True)
        self.le_server_address.setEnabled(True)
        self.le_server_port.setEnabled(True)
        self.le_plc_address.setEnabled(True)
        self.le_plc_port.setEnabled(True)

        self.set_FLAG_SERVER_CONNECTION(False)
        self.set_FLAG_PLC_CONNECTION(False)
        self.set_FLAG_WELDING(False)
        self.server_data_request_callback_func(False, 1)

    def btn_stop_func(self):
        self.btn_stop.setEnabled(False)
        self.stop()

        wait_thread = Thread(target=self.wait_stop, args=())
        wait_thread.start()

    def stop(self):
        self.__read_plc_thread.kill()
        self.__send_data_set_thread.kill()
        self.__send_current_status_thread.kill()
        self.__server_connection_thread.kill()

    def run(self):
        self.__server_connection_thread = server.ServerConnectionThread(self.server_address, self.server_port)
        self.__read_plc_thread = threads.ReadPlcThread(self)
        self.__send_data_set_thread = threads.SendDataSetThread(self)
        self.__send_current_status_thread = threads.SendCurrentStatusThread(self.send_current_status)

        self.__server_connection_thread.start()
        self.__read_plc_thread.start()
        self.__send_data_set_thread.start()
        self.__send_current_status_thread.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    edge_node = EdgeNode()
    edge_node.show()
    app.exec_()


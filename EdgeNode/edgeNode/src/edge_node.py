from pymodbus.client.sync import ModbusTcpClient
import time
import threads
import FaDAm as fd
from datetime import datetime
import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
import socketio


form_class = uic.loadUiType("ui/edgenode.ui")[0]


class EdgeNode(QMainWindow, form_class):

    data_set = None
    PID = 1
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

    def __init__(self):
        super().__init__()
        self.__read_plc_thread = threads.ReadPlcThread(self)
        self.__send_data_set_thread = threads.SendDataSetThread(self)
        self.__send_current_status_thread = threads.SendCurrentStatusThread(self)

        self.init_ui()

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

    def btn_stop_func(self):
        self.btn_run.setEnabled(True)
        self.le_server_address.setEnabled(True)
        self.le_server_port.setEnabled(True)
        self.le_plc_address.setEnabled(True)
        self.le_plc_port.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.stop()

    def connect_server(self):
        print(self.server_port)

    def disconnect_server(self):
        print(self.server_port)

    def stop(self):
        self.__read_plc_thread.kill()
        self.__send_data_set_thread.kill()
        self.__send_current_status_thread.kill()

        self.disconnect_server()

    def run(self):
        self.connect_server()

        self.__read_plc_thread.start()
        self.__send_data_set_thread.start()
        self.__send_current_status_thread.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    edge_node = EdgeNode()
    edge_node.show()
    app.exec_()


from threading import Thread
from pymodbus.client.sync import ModbusTcpClient
import edge_node
import time
from datetime import datetime


class CustomThread(Thread):
    clock_time = 0.1
    FLAG_PAUSE = False
    FLAG_KILL = False

    def __init__(self):
        Thread.__init__(self)
        self.base_time = time.time()

    def sync(self):
        distance = (time.time() - self.base_time) // self.clock_time
        while True:
            after = (time.time() - self.base_time) // self.clock_time
            if after == distance + 1:
                break
            else:
                time.sleep(self.clock_time / 100)


class ReadPlcThread(CustomThread):
    plc_address = '172.30.1.20'
    plc_port = 5020
    plc_client = None

    FLAG_WELDING = False

    init_current = 8.0
    init_voltage = 0.0
    init_wire_feed = 0.0

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.clock_time = 0.1

    def connect_plc(self):
        self.plc_client = ModbusTcpClient(self.plc_address, port=self.plc_port)
        self.plc_client.connect()

    def disconnect_plc(self):
        self.plc_client.close()
        self.plc_client = None

    def read_plc(self):
        self.sync()
        when = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        read_data = self.plc_client.read_holding_registers(0, 3)
        if read_data.isError():
            print("data read error!!")
            return [when, None, None, None]
        else:
            return [when, read_data.registers[0], read_data.registers[1], read_data.registers[2]]

    def add_data_to_data_set(self):
        print(self.clock_time)

    def check_current_data(self):
        if self.data.current_data[0] is None:
            return None
        elif self.data.current_data[0] >= self.init_current and self.data.current_data[1] >= self.init_voltage and \
                self.data.current_data[2] >= self.init_wire_feed:
            return True
        else:
            return False

    def run(self):
        self.FLAG_KILL = False
        self.FLAG_PAUSE = False
        self.connect_plc()

        while not self.FLAG_KILL:
            self.data.current_data = self.read_plc()
            print("*************************************")
            print("time : ", self.data.current_data[0])
            print("curr : ", self.data.current_data[1])
            print("volt : ", self.data.current_data[2])
            print("wire : ", self.data.current_data[3])
            # is_welding_data = self.check_current_data()
            # if is_welding_data is None:
            #     if self.data.FLAG_WELDING:
            #         self.add_data_to_data_set()
            # else:
            #     if self.data.FLAG_WELDING:
            #         if is_welding_data is True:
            #             self.add_data_to_data_set()
            #         elif is_welding_data is False:
            #             self.data.FLAG_WELDING = False
            #             # data 전송하기
            #             self.data.data_set = None
            #     else:
            #         if is_welding_data is True:
            #             # 자 이제 시작이야~
            #             print(1)

            while self.FLAG_PAUSE:
                time.sleep(0.1)

    def pause(self):
        self.FLAG_PAUSE = True

    def resume(self):
        self.FLAG_PAUSE = False

    def kill(self):
        self.FLAG_KILL = True

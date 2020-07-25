from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore.context import *


def run_server():
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [17] * 100),
        co=ModbusSequentialDataBlock(0, [17] * 100),
        hr=ModbusSequentialDataBlock(0, [17] * 100),
        ir=ModbusSequentialDataBlock(0, [17] * 100))

    print("PLC Server ON ( 172.30.1.20 : 5020 )")
    context = ModbusServerContext(slaves=store, single=True)
    StartTcpServer(context, address=("172.30.1.20", 5020))

from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore.context import *


def run_server():
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [17] * 100),
        co=ModbusSequentialDataBlock(0, [17] * 100),
        hr=ModbusSequentialDataBlock(0, [17] * 100),
        ir=ModbusSequentialDataBlock(0, [17] * 100))

    print("PLC Server ON ( localhost : 5020 )")
    context = ModbusServerContext(slaves=store, single=True)
    StartTcpServer(context, address=("localhost", 5020))

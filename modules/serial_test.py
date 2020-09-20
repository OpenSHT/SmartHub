import serial.tools.list_ports
from time import sleep

ports = list(serial.tools.list_ports.comports())

if ports is not None:
    for p in ports:
        print(f"Choose part of this string as your IDENTIFIER:\n  {p[1]}\n"
              f"Your port is:\n {p[0]}")
        sleep(.5)

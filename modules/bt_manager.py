from bluetooth import discover_devices, BluetoothSocket, lookup_name, RFCOMM
from bluetooth.btcommon import BluetoothError
from time import sleep
from threading import Thread, Event
import re
from modules.extras import Colors

class BTManager():
    def __init__(self, device_dict, sensor_q, bt_on):
        self.output = sensor_q
        self.target_name = "ESP32"
        self.target_addresses = []
        self.target_rooms = []
        self.sensor_threads = []
        self.lessThanExpected = True
        self.saved_bt_devices = device_dict
        self.bt_on = bt_on
        self.p = Colors()

    def bt_toggle(self, on_off):
        self.bt_on = on_off

    def new_device(self, new_device):
        """  """
        self.new = new_device
        for key, value in self.new:
            new_key = key
            new_value = value
            self.saved_bt_devices[key] = new_value

        found = False
        while not found:
            nearby_devices = discover_devices(duration=10, flush_cache=True,)
            for bdaddr in nearby_devices:
                if new_value == bdaddr:
                    self.target_addresses.append(new_value)
                    self.target_rooms.append(new_key)
                    i = len(self.target_addresses)
                    new_thread = Thread(target=self.data_thread, args=(new_value, new_key, self.output, i))
                    self.sensor_threads.append(new_thread)
                    new_thread.start()


    def data_thread(self, address, room, output_q, num):
        error_count = 0
        port_num = num

        while True:
            try:
                socket = BluetoothSocket( RFCOMM )
                socket.connect((address, 1))
                print(f"{self.p.START} {num}: Connected to: {address} {self.p.ENDC}")
                socket.settimeout(10.0)
                socket.send("x")
                break

            except BluetoothError:
                print(f"{self.p.WARN} {num}: connection timed out {self.p.ENDC}")
                sleep(1)
                continue

        while True:
            try:
                # Receive data from the BT Device
                data = socket.recv(200)
                data_decode = data.replace(b'\r\n', b'').decode()
                # print(data)
                
                try:
                    data_decode = data_decode.strip('\n').split(',')
                    # print(data_decode)
                    if len(data_decode) == 2:
                        temperature, humidity = data_decode
                        temperature = temperature.strip('/n')
                        humidity = humidity.strip('/n')
                        data_decode = [ temperature, humidity ]

                        self.output.put({f"{room}": data_decode}, block=False, timeout=2)

                    elif len(data_decode) > 2:
                        middle = data_decode[1]
                        middle = middle.split('\r\n')
                        data_decode = [ middle[1], data_decode[2] ]

                        temperature, humidity = data_decode
                        temperature = temperature.strip('/n')
                        humidity = humidity.strip('/r').strip('/n')
                        data_decode = [ temperature, humidity ]

                        self.output.put({f"{room}": data_decode}, block=False, timeout=2)

                    else:
                        pass
                        # print(f"{num}: missed data: {data_decode}")

                except:
                    # print(num, "-None: ", data_decode)
                    data_decode = None
                    pass                

                sleep(2)
                
            except KeyboardInterrupt:
                print(f"{num}: Closing Connection")
                socket.close()
                error_count += 1
                break
            except BluetoothError:
                print(f"{num}: connection timed out")
                socket.close()
                error_count += 1
                break
            except UnicodeDecodeError:
                print(f"{num}: UnicodeDecodeError")
                pass

    def connect_all(self):
        fail_count = 0
        if self.saved_bt_devices != {}:
            while self.lessThanExpected:
                nearby_devices = discover_devices(duration=10, flush_cache=True,)
                for bdaddr in nearby_devices:
                    # print("AD: ", bdaddr, lookup_name( bdaddr ))
                    device_name = str(lookup_name( bdaddr ))
                    if self.target_name in device_name:
                        # print("FOUND: ", bdaddr, lookup_name( bdaddr ))
                        for key, value in self.saved_bt_devices.items():
                            if(value[0] == str(bdaddr)):
                                location_key = key
                                self.target_addresses.append(bdaddr)
                                self.target_rooms.append(location_key)
                            else:
                                # print("Found unlisted ESP device: ", bdaddr)
                                pass
                                
                print(f"{self.p.START} Found: {len(self.target_addresses)} Devices {self.p.ENDC}")

                if len(self.target_addresses) == len(self.saved_bt_devices.keys()):
                    self.lessThanExpected = False
                elif fail_count == 3:
                    fail_count = 0
                    print(f"{self.p.WARN} Cant find all the sensors, continuing... {self.p.ENDC}")
                else:
                    self.target_addresses = []
                    print(f"{self.p.WARN} Rescanning for remaining devices... {self.p.ENDC}")
                    fail_count += 1

            try:
                if len(self.target_addresses) > 0:
                    i = 1
                    
                    for index in range(len(self.target_addresses)):
                        # print("found target bluetooth device with address ", self.target_addresses[index])
                        new_thread = Thread(target=self.data_thread, args=(self.target_addresses[index], self.target_rooms[index], self.output, i))
                        i += 1
                        self.sensor_threads.append(new_thread)

                    try:
                        for thread in self.sensor_threads:
                            thread.start()
                    except:
                        print("ERROR starting connections")
                    finally:
                        """ This section needs to maintain and reconnect to all known BLUETOOTH Devices






                        """
                else:
                    print("could not find target bluetooth devices nearby")
            except:
                for thread in self.sensor_threads:
                    thread.join()
                pass

        else:
            print("NO BLUETOOTH DEVICES SAVED")
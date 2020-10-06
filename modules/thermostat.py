import re
from time import time, sleep, localtime
from modules.extras import Colors
# import Adafruit_DHT
# import RPi.GPIO as GPIO

METHOD = ["serial", "gpio", "wifi"]
MICRO_CONTROLLERS = ["arduino", "esp32", "esp8266", "msp430"]
SBC = ["rpi", "orangepi", "rockpi"]


class Sensors:
    def __init__(self,
                 method="serial",       # ["gpio", "serial", "wifi"]
                 device="esp32",      # ["arduino", "esp32", "esp8266", "msp430", "rpi", "orangepi", "rockpi"]
                 identifier="CP2102",  # For Micro-Cont. use string || For GPIO use ["DHT22", "DS18B20", etc]
                 gpio_pin=4,          # Depends on your sensor/setup, 4 is good for most 1-Wire devices
                 baud_rate=9600):     # [9600, ..., 115200, ...]

        global METHOD, MICRO_CONTROLLERS, SBC

        p = Colors()
        self.method = str(method)
        self.device = str(device)
        self.identifier = str(identifier)
        # print(self.method, self.device, self.identifier)

        if self.method == METHOD[0]:  # Serial
            """This if statement is entirely in-case devices need separate methods"""
            if self.device in MICRO_CONTROLLERS:

                import serial.tools.list_ports

                ports = list(serial.tools.list_ports.comports())
                self.baud_rate = int(baud_rate)

                for port in ports:
                    if self.identifier in port[1]:
                        # print(port)
                        serial_port = str(port[0])
                        self.microC = serial.Serial(serial_port, self.baud_rate, timeout=3)
                        self.microC.flushInput()
                    else:
                        print("Micro-Controller Port NOT FOUND, check your identifier string")
                        break  # not pretty, need to callback so main program can handle

                    # self.reset_controller()
            else:
                print(f"{p.FAIL} {self.device} has not been added to the list\n "
                      f"Look at the list MICRO_CONTROLLERS in ///static/thermostat.py\n "
                      f"OR: if unique method, add it to Sensors(){p.ENDC}")

        elif self.method == METHOD[1]:  # GPIO
            self.gpio_pin = gpio_pin
            """This if statement is entirely in-case devices need separate methods"""
            if self.device in SBC:

                if self.identifier == "DHT22":
                    self.gpio_sensor = Adafruit_DHT.DHT22

                elif self.identifier == "DHT21":
                    self.gpio_sensor = Adafruit_DHT.DHT21

                elif self.identifier == "DHT11":
                    self.gpio_sensor = Adafruit_DHT.DHT11
                else:
                    print(f"{p.FAIL} {self.identifier} has not been integrated\n "
                          f"Look in ///static/thermostat.py:\n class Sensors():\n    def __init__(self, ...{p.ENDC}")

        elif self.method == METHOD[2]:  # WiFi
            print(f"{p.FAIL} Wifi-Socket method has not been integrated ye :/\n "
                  f"Feel free to contribute {p.ENDC}")

        else:
            print(f"{p.FAIL} {self.method} has not been integrated {p.ENDC}")

    def reset_controller(self):
        wait_till_ready = self.microC.readline().decode()[:-2]
        self.microC.write(b"reboot")  # Make Sure MCC code has a catch and software reset
        sleep(6)  # Allow reboot time before attempting read

    def get_data(self):
        global METHOD
        """Whatever the source, format: <hum,temp>: <59.6,22.3>"""
        try:
            if self.method == METHOD[0]:
                data = self.microC.readline().decode()[:-2]  # the last bit gets rid of the new-line char
                data_list = re.sub('<|>', '', str(data)).split(',')
            elif self.method == METHOD[1]:
                data_list = Adafruit_DHT.read_retry(self.gpio_sensor, self.gpio_pin)
            elif self.method == METHOD[2]:
                print("No WiFi Integration Yet")
                raise Exception
            else:
                raise Exception

            humidity = round(float(data_list[0]), 2)
            temperature = round(float(data_list[1]), 2)
            # print(temperature, humidity)
            return temperature, humidity

        except Exception:
            return 00.0, 00.0


class HvacLogic:
    """ Callable functions 
    """
    def get_action(self, data):
        if data[0] == 4:
            return self.highest_priority(data[1], data[2], data[3])
        elif data[0] == 3:
            return self.high_priority(data[1], data[2], data[3])
        elif data[0] == 2:
            return self.med_priority(data[1], data[2], data[3])
        elif data[0] == 1:
            return self.low_priority(data[1], data[2], data[3])

    def highest_priority(self, setpoint, temp, hum):

        if abs(setpoint - temp) >= 0.25:
            return [4, temp, hum]
        else:
            return None

    def high_priority(self, setpoint, temp, hum):
        
        if abs(setpoint - temp) >= 0.5:
            return [3, temp, hum]
        else:
            return None

    def med_priority(self, setpoint, temp, hum):

        if abs(setpoint - temp) >= 1.0:
            return [2, temp, hum]
        else:
            return None

    def low_priority(self, setpoint, temp, hum):

        if abs(setpoint - temp) >= 2.0:
            return [1, temp, hum]
        else:
            return None

class HvacControl:
    """ GPIO Relay Control
    - no way around commenting this out for testing,
    I recommend connecting the relay board to some actual LEDS
    this way you can make sure it performs as expected
    """
    HEAT = 22
    COOL = 27
    FAN_L = 17
    FAN_M = 23
    FAN_H = 24
    CHANNELS = [HEAT, COOL, FAN_L, FAN_M, FAN_H]
    # GPIO.setmode(GPIO.BCM)
    # GPIO.setwarnings(False)
    # GPIO.setup(CHANNELS, GPIO.OUT, initial=GPIO.HIGH)  # <--Not sure why but everything is backwards
    # GPIO.output(CHANNELS, GPIO.HIGH)

    temperature = 0.0
    humidity = 0.0
    mode = 'off'
    awake_time = 450
    sleep_time = 1305
    currently_awake = True
    currently_home = True
    active_wires = [0,0]

    def sp_change(self, new_sps, new_times):
        """"""
        self.home_setpoint = float(new_sps[0])
        self.away_setpoint = float(new_sps[1])
        self.sleep_setpoint = float(new_sps[2])
        self.awake_time = new_times[0]
        self.sleep_time = new_times[1]
        
        self.currently_awake = self.get_home_awake([self.awake_time, self.sleep_time])
        
    def mode_change(self, new_mode):
        """"""
        self.mode = new_mode

    def get_home_awake(self, home_awake, get=False):
        if len(home_awake) > 0:
            awake_tm = home_awake[0]
            sleep_tm = home_awake[1]
        else:
            awake_tm = self.awake_time
            sleep_tm = self.sleep_time

        if 'PM' in awake_tm:
            awake_tm = awake_tm.strip('PM').split(':')
            awake_min = ((int(awake_tm[0]) + 12) * 60) + int(awake_tm[1])
        else:
            awake_tm = awake_tm.strip('AM').split(':')
            awake_min = (int(awake_tm[0]) * 60) + int(awake_tm[1])

        if 'PM' in sleep_tm:
            sleep_tm = sleep_tm.strip('PM').split(':')
            sleep_min = ((int(sleep_tm[0]) + 12) * 60) + int(sleep_tm[1])
        else:
            sleep_tm = sleep_tm.strip('AM').split(':')
            sleep_min = (int(sleep_tm[0]) * 60) + int(sleep_tm[1])

        result = localtime(time())

        current_hour = result.tm_hour
        current_min = result.tm_min

        current_tm = (current_hour * 60) + current_min

        if current_tm >= awake_min and current_tm < sleep_min:
            if get:
                if len(home_awake) > 0:
                    current_index = 0
                    return current_index
                else:                        
                    return self.home_setpoint
            else:
                return True
        else:
            if get:
                if len(home_awake) > 0:
                    current_index = 1
                    return current_index
                else:
                    return self.sleep_setpoint
            else:
                return False

    def heat_high(self, p):
        print(f"{p.FAIL}   Heat  ||  Fan-High  ))) {p.ENDC} ")
        # GPIO.output(self.CHANNELS, GPIO.HIGH)
        # GPIO.output([self.HEAT, self.FAN_H], GPIO.LOW)
    
    def heat_med(self, p):
        print(f"{p.FAIL}   Heat  ||  Fan-Med  )) {p.ENDC} ")
        # GPIO.output(self.CHANNELS, GPIO.HIGH)
        # GPIO.output([self.HEAT, self.FAN_M], GPIO.LOW)

    def heat_low(self, p):
        print(f"{p.FAIL}   Heat  ||  Fan-Low  ) {p.ENDC} ")
        # GPIO.output(self.CHANNELS, GPIO.HIGH)
        # GPIO.output([self.HEAT, self.FAN_L], GPIO.LOW)

    def cool_high(self, p):
        print(f"{p.BLUE}   Cool  ||  Fan-High  ))) {p.ENDC} ")
        # GPIO.output(self.CHANNELS, GPIO.HIGH)
        # GPIO.output([self.COOL, self.FAN_H], GPIO.LOW)

    def cool_med(self, p):
        print(f"{p.BLUE}   Cool  ||  Fan-Med  )) {p.ENDC} ")
        # GPIO.output(self.CHANNELS, GPIO.HIGH)
        # GPIO.output([self.COOL, self.FAN_M], GPIO.LOW)

    def cool_low(self, p):
        print(f"{p.BLUE}   Cool  ||  Fan-Low  ) {p.ENDC} ")
        # GPIO.output(self.CHANNELS, GPIO.HIGH)
        # GPIO.output([self.COOL, self.FAN_L], GPIO.LOW)

    def all_off(self, p):
        # GPIO.output(self.CHANNELS, GPIO.HIGH)
        print(f"{p.FAIL} *  All OFF  * {p.ENDC} ")
        self.active_wires = [0,0]
        
    def relay_control(self, temp=21.0, hum=50.0, priority=3, mode="off"):
        p = Colors()
        self.temperature = temp
        self.humidity = hum
        self.mode = mode
        self.priority = priority

        if self.currently_awake and self.currently_home:
            current_sp = self.home_setpoint
        else:
            current_sp = self.sleep_setpoint

        if self.humidity is not None and self.temperature is not None:

            if (self.temperature - current_sp) <= 0.00 and (self.mode == "auto" or self.mode == "heat"):
                if (self.temperature - self.home_setpoint) <= - 1.50:
                    if self.active_wires != [1,3]:
                        self.heat_high(p)
                        self.active_wires = [1,3]
                elif (self.temperature - current_sp) <= -0.75:
                    if self.active_wires != [1,2]:
                        self.heat_med(p)
                        self.active_wires = [1,2]
                elif (self.temperature - current_sp) <= -0.25:
                    if self.active_wires != [1,1]:
                        self.heat_low(p)
                        self.active_wires = [1,1]
                else:
                    self.all_off(p)
                    pass

            elif (self.temperature - current_sp) >= 0.00 and (self.mode == "auto" or self.mode == "cool"):
                if (self.temperature - self.home_setpoint) >= 1.50:
                    if self.active_wires != [2,3]:
                        self.cool_high(p)
                        self.active_wires = [2,3]
                elif (self.temperature - current_sp) >= 0.75:
                    if self.active_wires != [2,2]:
                        self.cool_med(p)
                        self.active_wires = [2,2]
                elif (self.temperature - current_sp) >= 0.25:
                    if self.active_wires != [2,1]:
                        self.cool_low(p)
                        self.active_wires = [2,1]
                else:
                    self.all_off(p)
                    pass
            else:
                self.all_off(p)
                pass

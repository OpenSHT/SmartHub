from modules.thermostat import Sensors, HvacControl, HvacLogic
# from modules.extras import Colors
from modules.weather import Weather
from modules.bt_manager import BTManager
from modules.bt_listener import BTListener

from configparser import ConfigParser
from datetime import datetime
from threading import Thread, Event
from multiprocessing import Process, Queue, Event
from queue import Queue as tQueue

""" RUN OPTIONS:
"""
TESTING = True
BT = True
MINI_GUI = False

""" LOAD THE SAVED CONFIGURATION:
<==================================>
"""  
config = ConfigParser()
config.read('saved_config.ini')  # .ini File containing saved setting from the application

#  [ APP ]
BACKGROUND_TYPE = str(config.get('APP', 'background-type'))
BACKGROUND_POS =  str(config.get('APP', 'background-position'))
BACKGROUND_COLOR =  str(config.get('APP', 'background-color'))
BACKGROUND_FILE = str(config.get('APP', 'background-file'))
INTERFACE_THEME = str(config.get('APP', 'interface-color'))
# MINI_GUI = str(config.get('APP', 'mini-gui'))
if MINI_GUI:
    from modules.minigui import mini_gui as GUI
#  [ HVAC ]
setpoints = config.get('HVAC', 'setpoints').strip(' []').split(',')
HOME_SETPOINT = float(setpoints[0])  
AWAY_SETPOINT = float(setpoints[1])
SLEEP_SETPOINT = float(setpoints[2])
AWAKE_TIME = str(config.get('HVAC', 'awake_time'))
SLEEP_TIME = str(config.get('HVAC', 'sleep_time'))
MODE = str(config.get('HVAC', 'mode'))
LOCAL_SENSOR_PRIORITY = int(config.get('HVAC', 'local_sensor_priority'))

SETPOINTS = [ HOME_SETPOINT, AWAY_SETPOINT, SLEEP_SETPOINT ]
HOME_AWAY = [AWAKE_TIME, SLEEP_TIME]
#  [ WEATHER ]
LOCATION = str(config.get('WEATHER', 'location'))
OWM_API_KEY = str(config.get('WEATHER', 'owm_key'))
INTERFACE_UNITS = str(config.get('WEATHER', 'units'))

WEATHER_LOCATION = ""
RESULT_LIST = []
#  [ BT_DEVICES ]
try:
    if BT:
        BT_ROOMS = config.get('BT_DEVICES', 'bt_rooms').split(',')
        BT_MACS = config.get('BT_DEVICES', 'bt_macs').split(',')
        BT_PRIORITY = config.get('BT_DEVICES', 'bt_priorities').split(',')

        SAVED_BT_SENSORS = {}
        for i in range(len(BT_ROOMS)):
            SAVED_BT_SENSORS[BT_ROOMS[i]] = [ BT_MACS[i], int(BT_PRIORITY[i]) ]
    else:
        SAVED_BT_SENSORS = {}
except:
    SAVED_BT_SENSORS = {}

""" GLOBAL VARIABLES 
<==================================>
"""
# Local Sensor Options
METHOD = ["serial", "gpio"]
MICRO_CONTROLLER = ["arduino", "esp32", "esp8266"]
SBC = ["rpi", "orangepi", "rockpi"]
IDENT = {"USB_devices": ["CP2102", "USB2.0-Serial"],
         "GPIO_devices": ["DHT22", "DHT21", "DHT11"]}
GPIO_PIN = 4
BAUD = 9600
# Process safe Queues
bt_sensor_data = Queue()  # every BT device puts is data here, & gathered by dedicated Process(target=_check_bt_sensors)
action_q = Queue()  # Process(target=_check_bt_sensors) puts actions to Queue for the Thread(target=_check_sensors) to read
setpoint_q = Queue()
display_q = Queue()
# Shared data Queues for MiniGUI
sensor_data = tQueue()
# Local Sensor Variablea
local_temp = 0.0  
local_hum = 0.0
time_now = datetime.now().strftime("%H:%M")
# Control Thread/Process Loops
bt_dict = {}
ThreadList = []
ProcessList = []
SENSOR_DELAY = 2.0  # seconds
HVAC_DELAY = 20.0  # 600 seconds = (10 minutes)
global_action = 'on'
sensors_on = False  
bt_on = False
hvac_on = False
# Threading Events
exit_event = Event()
exit_event.clear()


""" SETUP CUSTOM OBJECTS AND METHODS 
<==================================>
"""
hvacControl = HvacControl()  # Will be used for function calls and the Control Thread
hvacLogic = HvacLogic()
weatherAPI = Weather(OWM_API_KEY)  # Used to make API calls and return data
bt_manager = BTManager(SAVED_BT_SENSORS, bt_sensor_data, bt_on)  # Connection manager
bt_listener = BTListener(bt_on, SAVED_BT_SENSORS)  # Connection listener

# Colorize those print statements
FAIL = '\033[1;31m'  # Red
START = '\033[1;32m'  # Green
WARN = '\033[1;33m'  # Yellow
BLUE = '\033[1;34m'  # Blue
CONT = '\033[1;35m'  # Purple
MSGS = '\033[1;36m'  # Cyan
ENDC = '\033[m'      # Normal

# HVAC Setup
hvacControl.sp_change(SETPOINTS, HOME_AWAY)  # Send saved setpoints and schedules
hvacControl.mode_change(MODE)  # Send saved control mode (auto, hot, cool, off)
c_index = hvacControl.get_home_awake(HOME_AWAY, get=True)  # checks current time against schedules & returns INDEX of appropriate setpoint
CURRENT_SP = float(SETPOINTS[c_index])  # Global for convenience

""" LOCAL SENSOR OPTIONS:
Sensors(
    method="gpio",       # ["gpio", "serial"]
    device="esp32",      # ["arduino", "esp32", "esp8266", "msp430", "rpi", "orangepi", "rockpi"]
    identifier="CP2102",  # For Micro-Cont. use string || For GPIO use ["DHT22", "DS18B20", etc]
    gpio_pin=4,          # Depends on your sensor/setup, 4 is good for most 1-Wire devices
    baud_rate=9600       # Defaults to 9600 if blank [9600, ..., 115200, ...]
    )

    NOTE:
    -   The "identifier" string is used for automatic serial-port detection,
        to find a unique identifier, run the "serial_test.py" file in the "modules" directory
    -   If your device isnt here, check out the methods in Sensors()("/modules/thermostat.py")
        unless it needs something unique, simply add it to the appropriate list
    EXAMPLES:
    -   Orange Pi with a DHT21 Sensor on the GPIO:
        -   sensor_cls = Sensors(METHOD[1], 
                                    SBC[1], 
                                    IDENT["GPIO_devices"][1], 
                                    GPIO_PIN)
    -   Arduino with a DHT22 Sensor outputting to Serial:
        -   sensor_cls = Sensors(METHOD[0], 
                                    MICRO_CONTROLLER[0], 
                                    IDENT["USB_devices"][1], 
                                    GPIO_PIN)
"""
if TESTING:
    # BELOW IS FOR READING FROM SERIAL (Laptop Dev)
    sensor_cls = Sensors(METHOD[0],
                        MICRO_CONTROLLER[0],
                        IDENT["USB_devices"][1],
                        GPIO_PIN,
                        BAUD)
else:
    # BELOW IS FOR THE RPi WITH A DHT22
    sensor_cls = Sensors(METHOD[1],
                         SBC[0],
                         IDENT["GPIO_devices"][2],  # 0: DHT22, 2: DHT11
                         GPIO_PIN)

# Formatting colors fancy print statements:

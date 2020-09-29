from flask import Flask, render_template, Response, jsonify, request, redirect, url_for
from time import sleep
from datetime import datetime
from threading import Thread, Event
from multiprocessing import Process
from multiprocessing import Queue as pQueue
import json
import sys
from configparser import ConfigParser
# My Modules("/modules"):
from modules.thermostat import Sensors, HvacControl
from modules.extras import Colors
from modules.weather import Weather
from modules.minigui import mini_gui
from modules.bt_classic import Bluetooth
from queue import Queue

app = Flask(__name__)

"""Get the saved configuration settings:
"""  
# <========================> #
config = ConfigParser()
config.read('saved_config.ini')

setpoints = config.get('HVAC', 'setpoints').strip(' []').split(',')
HOME_SETPOINT = float(setpoints[0])  
AWAY_SETPOINT = float(setpoints[1])
SLEEP_SETPOINT = float(setpoints[2])
SETPOINTS = setpoints

AWAKE_TIME = str(config.get('HVAC', 'awake_time'))
SLEEP_TIME = str(config.get('HVAC', 'sleep_time'))
HOME_AWAY = [AWAKE_TIME, SLEEP_TIME]

mode = str(config.get('HVAC', 'mode'))
LOCATION = str(config.get('WEATHER', 'location'))
OWM_API_KEY = str(config.get('WEATHER', 'owm_key'))
# GENERAL SETTINGS PAGE
BACKGROUND_TYPE = str(config.get('APP', 'background-type'))
BACKGROUND_POS =  str(config.get('APP', 'background-position'))
BACKGROUND_COLOR =  str(config.get('APP', 'background-color'))
BACKGROUND_FILE = str(config.get('APP', 'background-file'))
INTERFACE_THEME = str(config.get('APP', 'interface-color'))
INTERFACE_UNITS = str(config.get('WEATHER', 'units'))
WEATHER_LOCATION = ""
RESULT_LIST = []
MINI_GUI = bool(config.get('APP', 'mini-gui'))

BT_ROOMS = config.get('BT_DEVICES', 'bt_rooms').split(',')
BT_MACS = config.get('BT_DEVICES', 'bt_macs').split(',')
BT_PRIORITY = config.get('BT_DEVICES', 'bt_priorities').split(',')
SAVED_BT_SENSORS = {}

for i in range(len(BT_ROOMS)):
    SAVED_BT_SENSORS[BT_ROOMS[i]] = [ BT_MACS[i], BT_PRIORITY[i] ]

bt_sensor_data = pQueue()
setpoint_q = pQueue()
action_q = pQueue()
bluetooth_cls = Bluetooth(SAVED_BT_SENSORS, bt_sensor_data)
# <========================> #

""" **** SETUP YOUR SENSOR!!!! ****:
Sensors(
    method="gpio",       # ["gpio", "serial", "wifi"]
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
# <========================> #
METHOD = ["serial", "gpio", "wifi"]
MICRO_CONTROLLER = ["arduino", "esp32", "esp8266", "msp430"]
SBC = ["rpi", "orangepi", "rockpi"]
IDENT = {"USB_devices": ["CP2102", "USB2.0-Serial"],
         # ["ESP32 with CP2102 chip", For some reason Arduinos can be very generic]
         "GPIO_devices": ["DHT22", "DHT21", "DHT11"]}
GPIO_PIN = 4
BAUD = 9600
# Create a 2nd Sensor class if more than one
# <========================> #
# BELOW IS FOR THE RPi WITH A DHT22
# sensor_cls = Sensors(METHOD[1],
#                      SBC[0],
#                      IDENT["GPIO_devices"][0],
#                      GPIO_PIN)
# <========================> #
# BELOW IS FOR READING FROM SERIAL
sensor_cls = Sensors(METHOD[0],
                     MICRO_CONTROLLER[0],
                     IDENT["USB_devices"][1],
                     GPIO_PIN,
                     BAUD)
SENSOR_DELAY = 2.0  # seconds

p = Colors()
hvac_cls = HvacControl()
hvac_cls.sp_change(SETPOINTS, HOME_AWAY)
hvac_cls.mode_change(mode)
c_index = hvac_cls.get_home_awake(HOME_AWAY, get=True)
CURRENT_SP = SETPOINTS[c_index]

weather_cls = Weather(OWM_API_KEY)

# Shared data Queues for MiniGUI
sensor_data = Queue()

primary_temp = 0.0
primary_hum = 0.0
time_now = datetime.now().strftime("%H:%M")
hvac_loop = 600.0  # seconds (10 minutes)


global_action = 'on'
sensors_on = False  # to control loop in thread
bt_on = False
hvac_on = False
exit_event = Event()
exit_event.clear()

def _hvac_control():
    """THREAD: Runs every 10 minutes (600 sec)
            :returns primary_temp, primary_hum
    """
    global sensors_on, primary_temp, primary_hum, mode, hvac_loop, hvac_cls, SETPOINTS, HOME_AWAY, exit_event

    sleep(2)
    print(f"{p.START} |*** Start of HVAC Thread ***| {p.ENDC} \n")
    
    while hvac_on:

        hvac_cls.relay_control(primary_temp, primary_hum, mode)

        if exit_event.is_set():
            break

        sleep(hvac_loop)
    
    print(f"{p.WARN} |*** Stopping HVAC Thread ***|{p.ENDC} \n")


def _check_sensors():
    """THREAD: Runs every 1 second
        :returns primary_temp, primary_hum
    """
    global sensors_on, hvac_on, global_action, primary_temp, primary_hum, time_now, sensor_cls, hvac_cls, SETPOINTS, HOME_AWAY, SENSOR_DELAY, CURRENT_SP, exit_event, action_q

    print(f"{p.START} |*** Start of Sensor Thread ***| {p.ENDC} \n")
    count = 0
    zero_count = 0

    while sensors_on:  # global variable to stop loop
        # Get Primary Sensor Data:
        try:
            primary_temp, primary_hum = sensor_cls.get_data()
            if primary_temp == 0.0:
                zero_count += 1
                if zero_count == 3:
                    global_action = "sensors_off"
                    hvac_on = False
        except TypeError:
            print(f"{p.FAIL} [ERROR]: Received weird data{p.ENDC} \n")

        time_now = datetime.now().strftime("%H:%M")
        count += 1
        
        if hvac_on and count == 60 and abs(CURRENT_SP - primary_temp) > 1.5:
            count = 0
            hvac_cls.relay_control(primary_temp, primary_hum, mode)

        if exit_event.is_set():
            break

        sleep(SENSOR_DELAY)

    print(f"{p.WARN} |*** Stopping Sensor Thread ***| {p.ENDC} \n")

def _check_bt_sensors(data_q, set_point_q, action_q, get_sp):
    data_q = data_q
    current_setpoint = get_sp([], get=True)

    def highest_priority(temp, hum, current_sp):
        """"""
        if abs(current_sp - temp) >= 0.5:
            print(f"Priority HIGHEST, turning on HVAC:  {temp}, {hum}")
        else:
            print(f"Priority HIGHEST, doing nothing:  {temp}, {hum}")

    def high_priority(temp, hum, current_sp):
        """"""
        if abs(current_sp - temp) >= 0.75:
            print(f"Priority HIGH, turning on HVAC:  {temp}, {hum}")
        else:
            print(f"Priority HIGH, doing nothing:  {temp}, {hum}")

    def med_priority(temp, hum, current_sp):
        """"""
        if abs(current_sp - temp) >= 1.25:
            print(f"Priority MED, turning on HVAC:  {temp}, {hum}")
        else:
            print(f"Priority MED, doing nothing:  {temp}, {hum}")

    def low_priority(temp, hum, current_sp):
        """"""
        if abs(current_sp - temp) >= 2.0:
            print(f"Priority LOW, turning on HVAC:  {temp}, {hum}")
        else:
            print(f"Priority LOW, doing nothing:  {temp}, {hum}")

    while bt_on:
        try:
            current_setpoint = get_sp([], get=True)
        except:
            pass

        try:
            reading = data_q.get(block=True, timeout=2)

            for key in SAVED_BT_SENSORS:
                if key in reading.keys():
                    temperature = reading[key][0]
                    humidity = reading[key][1].strip('/r')
                    if SAVED_BT_SENSORS[key][1] == "highest":
                        highest_priority(float(temperature), float(humidity), float(current_setpoint))
                    elif SAVED_BT_SENSORS[key][1] == "high":
                        high_priority(float(temperature), float(humidity), float(current_setpoint))
                    elif SAVED_BT_SENSORS[key][1] == "med":
                        med_priority(float(temperature), float(humidity), float(current_setpoint))
                    elif SAVED_BT_SENSORS[key][1] == "low":
                        low_priority(float(temperature), float(humidity), float(current_setpoint))
                    else:
                        print(SAVED_BT_SENSORS[key][1])

        except KeyboardInterrupt:
            print("Closing Connections")
            # for thread in sensor_threads:
            #     thread.join()
            break
        
        except Exception as e:
            print(e)
            pass

# def get_current_sp(sp_change=None):
#     global SETPOINTS, HOME_AWAY

#     changed_sp = sp_change
#     current_index = 0

#     if 'PM' in HOME_AWAY[0]:
#         awake_tm = HOME_AWAY[0].strip('PM').split(':')
#         awake_min = ((int(awake_tm[0]) + 12) * 60) + int(awake_tm[1])
#     else:
#         awake_tm = HOME_AWAY[0].strip('AM').split(':')
#         awake_min = (int(awake_tm[0]) * 60) + int(awake_tm[1])

#     if 'PM' in HOME_AWAY[1]:
#         sleep_tm = HOME_AWAY[1].strip('PM').split(':')
#         sleep_min = ((int(sleep_tm[0]) + 12) * 60) + int(sleep_tm[1])
#     else:
#         sleep_tm = HOME_AWAY[1].strip('AM').split(':')
#         sleep_min = (int(sleep_tm[0]) * 60) + int(sleep_tm[1])

#     result = localtime(time())

#     current_hour = result.tm_hour
#     current_min = result.tm_min

#     current_tm = (current_hour * 60) + current_min

#     if current_tm >= awake_min and current_tm < sleep_min:
#         current_index = 0
#         if changed_sp:
#             return current_index
#         else:
#             return SETPOINTS[current_index]
#     else:
#         current_index = 1
#         if changed_sp:
#             return current_index
#         else:
#             return SETPOINTS[current_index]

#     else:



@app.route("/")
@app.route("/thermostat", methods=['POST', 'GET'])
@app.route("/thermostat/<action>", methods=['POST', 'GET'])
def thermostat(action='on'):
    """THERMOSTAT PAGE
    """
    global global_action  #, sensors_on, hvac_on, primary_temp, primary_hum, time_now, mode, CURRENT_SP, LOCATION, weather_cls

    global_action = f"{action}"

    return render_template('hub/thermostat.html', title=" - Thermostat", sp=CURRENT_SP)


@app.route("/schedules", methods=['POST', 'GET'])
def schedules():

    if request.method == "POST":
        global AWAKE_TIME, SLEEP_TIME
        
        awake = request.form["awake-display"].strip(' ')
        sleep = request.form["sleep-display"].strip(' ')
        
        
        # print(awake, sleep)
        config.set('HVAC', 'awake_time', awake)
        config.set('HVAC', 'sleep_time', sleep)
        AWAKE_TIME = awake
        SLEEP_TIME = sleep

        with open('saved_config.ini', 'w') as f:
            config.write(f)

    return render_template("hub/schedules.html", title=" - Schedules")


@app.route("/rooms", methods=['POST', 'GET'])
def rooms():

    return render_template("hub/rooms.html", title=" - Rooms")


@app.route("/settings", methods=['POST', 'GET'])
@app.route("/settings/<page>", methods=['POST', 'GET'])
def settings(page=None):
    """SETTINGS PAGE
    """
    global BACKGROUND_TYPE, BACKGROUND_POS, INTERFACE_THEME, INTERFACE_UNITS, BACKGROUND_COLOR, BACKGROUND_FILE, WEATHER_LOCATION, weather_cls, RESULT_LIST, LOCATION

    if request.method == "POST":
        BACKGROUND_TYPE = request.form["image-type"]
        BACKGROUND_POS = request.form["image-position"]
        INTERFACE_THEME = request.form["interface-theme"]
        INTERFACE_UNITS = request.form["interface-unit"]
        BACKGROUND_COLOR = request.form["color-chooser"]

        if request.form["file-chooser"] != '':
            BACKGROUND_FILE = request.form["file-chooser"]

        WEATHER_LOCATION = request.form["location-search"]
        

        if WEATHER_LOCATION != '':
            RESULT_LIST = weather_cls.search_locations(WEATHER_LOCATION)
            WEATHER_LOCATION = ''
        else:
            RESULT_LIST = []

        if "search-results" in request.form:
            LOCATION = request.form["search-results"]
            config.set('WEATHER', 'location', LOCATION)


    # Write to Config File
        config.set('APP', 'background-type', BACKGROUND_TYPE)
        config.set('APP', 'background-position', BACKGROUND_POS)
        config.set('APP', 'background-color', BACKGROUND_COLOR)
        if BACKGROUND_FILE != "":
            config.set('APP', 'background-file', BACKGROUND_FILE)
        config.set('APP', 'interface-color', INTERFACE_THEME)
        config.set('WEATHER', 'units', INTERFACE_UNITS)

        with open('saved_config.ini', 'w') as f:
                    config.write(f)

        print("Here is your form data:\n")
        print(BACKGROUND_TYPE, BACKGROUND_POS, BACKGROUND_COLOR, BACKGROUND_FILE, INTERFACE_THEME, WEATHER_LOCATION, INTERFACE_UNITS, "\n")
        
    # RETURN THE SELECTED SESTTING PAGE
    if page:
        return render_template(f"hub/settings/{page}.html")
    else:
        return render_template("hub/settings.html", title=" - Settings")


@app.route('/_update_thermostat', methods=['POST'])
def update_sensor_data():
    """Request route for sensor and time data
    """
    global primary_temp, primary_hum, time_now, sensor_data

    d = datetime.strptime(time_now, "%H:%M")

    sensor_data.put([primary_temp, primary_hum])

    return jsonify({
        'temperature': str(primary_temp) + ' &#176;',
        'humidity': str(primary_hum) + ' %',
        'time_now': d.strftime("%-I:%M %p"),
    })


@app.route('/_mode_changed', methods=["POST"])
def _mode_changed():
    global mode, global_action, hvac_cls, hvac_on, sensors_on, config

    if request.method == "POST":
        try:
            new_mode = str(request.data, "utf-8")

            if mode == 'off' and new_mode != mode:
                # Turn back on from an off position
                print(f"{p.MSGS} Reloading... {p.ENDC} \n")
                mode = new_mode
                hvac_on = True
                hvac_cls.mode_change(mode)

                Thread(target=_hvac_control).start()

                config.set('HVAC', 'mode', mode)

                with open('saved_config.ini', 'w') as f:
                    config.write(f)

                return redirect(url_for('thermostat', action='on'))

            elif new_mode != mode:
                mode = new_mode
                print(f"{p.MSGS} [MODE CHANGE]: {mode} {p.ENDC} \n")
                config.set('HVAC', 'mode', mode)

                with open('saved_config.ini', 'w') as f:
                    config.write(f)

                if mode == 'off':
                    hvac_on = False
                    hvac_cls.mode_change(mode)
                    global_action = 'hvac_off'
                else:
                    hvac_cls.mode_change(mode)
                    hvac_cls.relay_control(primary_temp, primary_hum, mode)
                    global_action = 'on'

                return "mode changed"

            else:
                return "mode not changed"
        except Exception:
            print(f"{p.FAIL} [ERROR]: {p.ENDC} \n")

            return "[ERROR]: in 'def mode_changed():'"


@app.route('/_sp_changed', methods=["POST"])
def _sp_changed():
    global SETPOINTS, HOME_AWAY, CURRENT_SP, primary_temp, primary_hum, mode, hvac_on, config, setpoint_q
    
    if request.method == "POST":
        
        try:
            SETPOINTS[0] = float(request.form["away_temp"])
            SETPOINTS[1] = float(request.form["sleep_temp"])
            SETPOINTS[2] = float(request.form["home_temp"])

            config.set('HVAC', 'setpoints', str(SETPOINTS))

            with open('saved_config.ini', 'w') as f:
                config.write(f)

            print("SAVED NEW CONFIG\n")
            # Send to HVAC Thread
            hvac_cls.sp_change( SETPOINTS, HOME_AWAY )
            hvac_cls.relay_control(primary_temp, primary_hum, mode)
            # Send to BLUETOOTH Process
            setpoint_q.put( SETPOINTS, HOME_AWAY )

            return "setpoints changed"
        
        except KeyError:
            new_sp = float(request.form["current_temp_sp"])
            if new_sp != CURRENT_SP and hvac_on:
                CURRENT_SP = new_sp
                index = hvac_cls.get_home_awake(HOME_AWAY, get=True)
                SETPOINTS[index] = CURRENT_SP
                config.set('HVAC', 'setpoints', str(SETPOINTS))

                with open('saved_config.ini', 'w') as f:
                    config.write(f)

                print("SAVED NEW CONFIG\n")
                hvac_cls.sp_change( SETPOINTS, HOME_AWAY )
                hvac_cls.relay_control(primary_temp, primary_hum, mode)

            return "setpoint changed"

        except ValueError:
            print(f"{p.FAIL} [ERROR]: in 'def sp_changed()'{p.ENDC} \n")

            return "[ERROR]: in 'def sp_changed()'"
    else:
        return None


@app.route('/_get_config', methods=['POST'])
def _get_config():
    """"""
    global mode, HOME_SETPOINT, AWAY_SETPOINT, SLEEP_SETPOINT, AWAKE_TIME, SLEEP_TIME, BACKGROUND_TYPE, BACKGROUND_POS, INTERFACE_THEME, INTERFACE_UNITS, BACKGROUND_COLOR, BACKGROUND_FILE

    return jsonify({
        'hvac_mode': mode,
        'home_setpoint': HOME_SETPOINT,
        'away_setpoint': AWAY_SETPOINT,
        'sleep_setpoint': SLEEP_SETPOINT,
        'awake-time': AWAKE_TIME,
        'sleep-time': SLEEP_TIME, 
        'back-type': BACKGROUND_TYPE,
        'back-pos': BACKGROUND_POS,
        'int-theme': INTERFACE_THEME,
        'int-unit': INTERFACE_UNITS,
        'back-color': BACKGROUND_COLOR,
        'back-file': BACKGROUND_FILE,
        'result-list': RESULT_LIST
    })


@app.route('/_update_chart')
def _update_chart():
    """Request route for updating chart data
        NEEDS METHOD TO STOP IT FROM REFRESHING IF GENERATOR ALREADY RUNNING
    """
    global sensors_on, primary_temp, primary_hum, time_now, exit_event, FlaskServer, ThreadList

    def update_data():
        print(f"{p.START} |*** Start of Chart GENERATOR ***| {p.ENDC} \n")

        while sensors_on:  # global variable to stop loop
            d = datetime.strptime(time_now, "%H:%M")
            json_data = json.dumps(
                {'time': d.strftime("%-I:%M %p"), 'temp': float(primary_temp), 'hum': float(primary_hum), 'refresh': 'false'})
            yield f"data:{json_data}\n\n"

            if exit_event.is_set():
                # shutdown = 5  #request.environ.get('werkzeug.server.shutdown')
                # if shutdown is None:
                #     raise RuntimeError("the function is unavailable")
                # else:
                    # print(f"{p.WARN} CLOSING... {p.ENDC} \n")
                    # sys.exit()
                    # shutdown()

                for thread in ThreadList:
                    thread.join()
                break

            sleep(60)

        print(f"{p.WARN} |*** Stopping Chart Generator ***| {p.ENDC} \n")

    return Response(update_data(), mimetype='text/event-stream')


@app.route('/_update_weather', methods=['POST', 'GET'])
def _update_weather():
    global weather_cls, LOCATION, INTERFACE_UNITS
    weather_dict = weather_cls.update_owm(INTERFACE_UNITS, LOCATION)
    return jsonify(weather_dict)


""" MAIN RUN SECTION
"""
if __name__ == '__main__':
    ThreadList = []

    if mode == "off":
        global_action = "hvac_off"

        if hvac_on:
            hvac_on = False  # it should stop thread
            mode = 'off'
            print(f"{p.MSGS} HVAC is now off {p.ENDC} \n")
        else:
            print(f"{p.WARN} HVAC not running {p.ENDC} \n")

        if not sensors_on:
            sensors_on = True
            sensors = Thread(target=_check_sensors)  # Loops every 1 second (Sensor, Chart & Clock update)
            ThreadList.append(sensors)
        else:
            print(f"{p.WARN} Sensors already running {p.ENDC} \n")

        if bt_on:
            bt_on = False  # it should stop thread
            print(f"{p.MSGS} BT is now off {p.ENDC} \n")
        else:
            print(f"{p.WARN} BT not running {p.ENDC} \n")

    elif global_action == 'on':
        if not sensors_on:
            sensors_on = True
            sensors = Thread(target=_check_sensors)  # Loops every 1 second (Sensor, Chart & Clock update)
            ThreadList.append(sensors)
        else:
            print(f"{p.WARN} Sensors already on {p.ENDC} \n")

        if not hvac_on:
            hvac_on = True
            hvac = Thread(target=_hvac_control)  # Loops every 10 minutes (Relay Control)
            ThreadList.append(hvac)
        else:
            print(f"{p.WARN} HVAC already on {p.ENDC} \n")

        if not bt_on:
            bt_on = True  # it starts thread
            bt_classic = Process(target=_check_bt_sensors, args=(bt_sensor_data, setpoint_q, action_q, hvac_cls.get_home_awake))
            bt_classic.start()
        else:
            print(f"{p.WARN} BT already on {p.ENDC} \n")

    elif global_action == 'sensors_off':
        if sensors_on:
            sensors_on = False  # it should stop thread
            print(f"{p.MSGS} Sensors are now off {p.ENDC} \n")
        else:
            print(f"{p.WARN} [WARNING] Sensors not running {p.ENDC} \n")

        if bt_on:
            bt_on = False  # it should stop thread
            print(f"{p.MSGS} BT is now off {p.ENDC} \n")
        else:
            print(f"{p.WARN} BT not running {p.ENDC} \n")

    else:
        print(f"{p.WARN} [WARNING] mode error {p.ENDC} \n")

    """ Support GUI for the 3" TFT touchscreen for SBC's ( GUIZERO [...for now] ) """
    if MINI_GUI:
        GUI = mini_gui
        small_gui = Thread( target=GUI, 
                args=(sensor_data, exit_event)
                )        
        ThreadList.append(small_gui)

    """ START BLUETOOTH SETUP """
    bt = Process(target=bluetooth_cls.connect_all)
    bt.start()

    """ INITIALIZE ALL THE THREADS:
        - Sensor Thread
        - HVAC Control Thread
        - Mini GUI for 3in TFT Thread
    """ 
    for thread in ThreadList:
        thread.start()

    """ Start the Flask Server as the MAIN / ROOT Thread """
    FlaskServer = Process(target=app.run(
                                        host="0.0.0.0",  # "open.sht",
                                        port="5050",
                                        debug=False,
                                        threaded=True))
    FlaskServer.start()

from flask import Flask, render_template, Response, jsonify, request, redirect, url_for
from time import sleep
from datetime import datetime
from threading import Thread, Event
from multiprocessing import Process
import json
from configparser import ConfigParser
# My Modules("/modules"):
from modules.thermostat import Sensors, HvacControl
from modules.extras import Colors
from modules.weather import Weather
from modules.minigui import mini_gui
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

AWAKE_TIME = str(config.get('HVAC', 'awake_time'))
SLEEP_TIME = str(config.get('HVAC', 'sleep_time'))

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
HOME_AWAY = [AWAKE_TIME, SLEEP_TIME]
hvac_cls = HvacControl()
hvac_cls.sp_change(setpoints, HOME_AWAY)
hvac_cls.mode_change(mode)

weather_cls = Weather(OWM_API_KEY)

# Shared data Queues for MiniGUI
sensor_data = Queue()

temp = 0.0
hum = 0.0
sensors_on = False  # to control loop in thread
time_now = datetime.now().strftime("%H:%M")
hvac_loop = 600.0  # seconds (10 minutes)
hvac_on = False

global_action = 'on'

exit_event = Event()
exit_event.clear()

def _hvac_control():
    """THREAD: Runs every 10 minutes (600 sec)
            :returns temp, hum
    """
    global sensors_on, temp, hum, mode, hvac_loop, hvac_cls, HOME_SETPOINT, exit_event

    sleep(2)
    print(f"{p.START} Start of HVAC-Thread {p.ENDC} \n")
    
    while hvac_on:
        hvac_cls.relay_control(temp, hum, mode)

        if exit_event.is_set():
            break

        sleep(hvac_loop)
    
    print(f"{p.WARN} Stopping HVAC-Thread {p.ENDC} \n")


def _check_sensors():
    """THREAD: Runs every 1 second
        :returns temp, hum
    """
    global sensors_on, hvac_on, global_action, temp, hum, time_now, sensor_cls, hvac_cls, HOME_SETPOINT, SENSOR_DELAY, exit_event

    print(f"{p.START} Start of Sensor-Thread {p.ENDC} \n")
    count = 0
    zero_count = 0

    while sensors_on:  # global variable to stop loop
        try:
            temp, hum = sensor_cls.get_data()
            if temp == 0.0:
                zero_count += 1
                if zero_count == 3:
                    global_action = "sensors_off"
                    hvac_on = False
        except TypeError:
            print(f"{p.FAIL} [ERROR]: Received weird data{p.ENDC} \n")

        time_now = datetime.now().strftime("%H:%M")
        count += 1

        if hvac_on and count == 60 and abs(HOME_SETPOINT - temp) > 1.5:
            count = 0
            hvac_cls.relay_control(temp, hum, mode)

        if exit_event.is_set():
            break

        sleep(SENSOR_DELAY)

    print(f"{p.WARN} Stopping Sensor-Thread {p.ENDC} \n")


@app.route("/")
@app.route("/thermostat", methods=['POST', 'GET'])
@app.route("/thermostat/<action>", methods=['POST', 'GET'])
def thermostat(action='on'):
    """THERMOSTAT PAGE
    """
    global global_action  #, sensors_on, hvac_on, temp, hum, time_now, mode, HOME_SETPOINT, LOCATION, weather_cls

    global_action = f"{action}"

    return render_template('hub/thermostat.html', title=" - Thermostat", sp=HOME_SETPOINT)


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
    global temp, hum, time_now, sensor_data

    d = datetime.strptime(time_now, "%H:%M")

    sensor_data.put([temp, hum])

    return jsonify({
        'temperature': str(temp) + ' &#176;',
        'humidity': str(hum) + ' %',
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
                    hvac_cls.relay_control(temp, hum, mode)
                    global_action = 'on'

                return "mode changed"

            else:
                return "mode not changed"
        except Exception:
            print(f"{p.FAIL} [ERROR]: {p.ENDC} \n")

            return "[ERROR]: in 'def mode_changed():'"


@app.route('/_sp_changed', methods=["POST"])
def _sp_changed():
    global HOME_SETPOINT, AWAY_SETPOINT, SLEEP_SETPOINT, AWAKE_TIME, SLEEP_TIME, temp, hum, mode, hvac_on, config
    
    if request.method == "POST":
        
        try:
            AWAY_SETPOINT = float(request.form["away_temp"])
            SLEEP_SETPOINT = float(request.form["sleep_temp"])
            HOME_SETPOINT = float(request.form["home_temp"])

            config.set('HVAC', 'setpoints', str([HOME_SETPOINT, AWAY_SETPOINT, SLEEP_SETPOINT]))

            with open('saved_config.ini', 'w') as f:
                config.write(f)

            print("SAVED NEW CONFIG\n")
            hvac_cls.sp_change([HOME_SETPOINT, AWAY_SETPOINT, SLEEP_SETPOINT], [AWAKE_TIME, SLEEP_TIME])
            hvac_cls.relay_control(temp, hum, mode)

            return "setpoints changed"
        
        except KeyError:
            new_sp = float(request.form["home_temp"])
            if new_sp != HOME_SETPOINT and hvac_on:
                HOME_SETPOINT = new_sp
                config.set('HVAC', 'setpoints', str([HOME_SETPOINT, AWAY_SETPOINT, SLEEP_SETPOINT]))

                with open('saved_config.ini', 'w') as f:
                    config.write(f)

                print("SAVED NEW CONFIG\n")
                hvac_cls.sp_change([HOME_SETPOINT, AWAY_SETPOINT, SLEEP_SETPOINT], [AWAKE_TIME, SLEEP_TIME])
                hvac_cls.relay_control(temp, hum, mode)

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
    global sensors_on, temp, hum, time_now, exit_event, FlaskServer, ThreadList

    def update_data():
        print(f"{p.START} [Start of Chart-Loop] {p.ENDC} \n")

        while sensors_on:  # global variable to stop loop
            d = datetime.strptime(time_now, "%H:%M")
            json_data = json.dumps(
                {'time': d.strftime("%-I:%M %p"), 'temp': float(temp), 'hum': float(hum), 'refresh': 'false'})
            yield f"data:{json_data}\n\n"

            if exit_event.is_set():
                for thread in ThreadList:
                    thread.join()

                FlaskServer.terminate()
                FlaskServer.join()
                break

            sleep(60)

        print(f"{p.WARN} [Stopping Chart-Loop] {p.ENDC} \n")

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
            print(f"{p.WARN} [WARNING] HVAC not running {p.ENDC} \n")
        if not sensors_on:
            sensors_on = True
            sensors = Thread(target=_check_sensors)  # Loops every 1 second (Sensor, Chart & Clock update)
            ThreadList.append(sensors)
        else:
            print(f"{p.WARN} Sensors already running {p.ENDC} \n")

    elif global_action == 'on':
        if not sensors_on:
            sensors_on = True
            sensors = Thread(target=_check_sensors)  # Loops every 1 second (Sensor, Chart & Clock update)
            ThreadList.append(sensors)
        else:
            print(f"{p.WARN} Sensors already running {p.ENDC} \n")

        if not hvac_on:
            hvac_on = True
            hvac = Thread(target=_hvac_control)  # Loops every 10 minutes (Relay Control)
            ThreadList.append(hvac)
        else:
            print(f"{p.WARN} HVAC already running {p.ENDC} \n")   

    elif global_action == 'sensors_off':
        if sensors_on:
            sensors_on = False  # it should stop thread
            print(f"{p.MSGS} Sensors are now off {p.ENDC} \n")
        else:
            print(f"{p.WARN} [WARNING] Sensors not running {p.ENDC} \n")

    else:
        print(f"{p.WARN} [WARNING] mode error {p.ENDC} \n")

    """ Support GUI for the 3" TFT touchscreen for SBC's ( GUIZERO [...for now] ) """
    if MINI_GUI:
        GUI = mini_gui
        small_gui = Thread( target=GUI, 
                args=(sensor_data, exit_event)
                )        
        ThreadList.append(small_gui)

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

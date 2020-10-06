from flask import Flask, render_template, Response, jsonify, request, redirect, url_for
from time import sleep
from datetime import datetime
from threading import Thread
from multiprocessing import Process
import json
import sys
# My Modules("/modules"):
from modules.settings import *

# FLASK APP
app = Flask(__name__)
WEB_PORT = "5050"
HOST_IP = "0.0.0.0"
DEBUG = False  # Causes if __name__ == '__main__' to run twice

def _hvac_control():
    """THREAD: Runs every 10 minutes (600 sec)
            :returns local_temp, local_hum
    """
    global sensors_on, local_temp, local_hum, MODE, HVAC_DELAY, hvacControl, hvacLogic, SETPOINTS, HOME_AWAY, exit_event, action_q

    delayed_start = 2
    sleep(delayed_start)
    print(f"{START} |*** Start of HVAC Thread ***| {ENDC} ")
    action_dict = {}
    list_length = 0
    
    while hvac_on:
        try:
            while not action_q.empty():
                actions = dict(action_q.get_nowait())  # { NAME: [ PRIORITY, TEMP, HUM ] }
                # print(f"ACTIONS: {actions}")
                for key in actions.keys():
                    action_dict[key] = actions[key]
            # print(action_dict)
            avg_temp = 0.0
            avg_hum = 0.0
            highest_priority = 0
            active_temps = []
            active_keys = []
            for key in action_dict.keys():
                if action_dict[key] and action_dict[key][0] >= highest_priority:                        
                    highest_priority = action_dict[key][0]

            for key in action_dict.keys():
                if action_dict[key] and action_dict[key][0] == highest_priority:
                    active_keys.append(key)
                    active_temps.append([action_dict[key][0], action_dict[key][1], action_dict[key][2]])

            list_length = len(active_keys)
           
            if list_length != 0:
                for i in range(list_length):
                    avg_temp += active_temps[i][1]
                    avg_hum += active_temps[i][2]
                avg_temp = avg_temp / list_length
                avg_hum = avg_hum / list_length
                priority = active_temps[i][0]
                # Activate Relay Control:
                hvacControl.relay_control(avg_temp, avg_hum, priority, MODE)
                print(f"{START} SENT: {avg_temp}, KEYS: {active_keys}, MODE: {MODE} {ENDC}")

        except Exception as e:
            print(e)
            pass

        if exit_event.is_set():
            break
        sleep(HVAC_DELAY)
    
    print(f"{WARN} |*** Stopping HVAC Thread ***|{ENDC} ")
    hvacControl.relay_control(0.0, 0.0, 'off')


def _check_sensors():
    """THREAD: Runs every 1 second
        :returns local_temp, local_hum
    """
    global sensors_on, hvac_on, global_action, local_temp, local_hum, time_now, sensor_cls, hvacControl,\
    SETPOINTS, HOME_AWAY, SENSOR_DELAY, CURRENT_SP, LOCAL_SENSOR_PRIORITY, exit_event, action_q

    bad_readings = 0
    reading_accepted = True
    print(f"{START} |*** Start of Sensor Thread ***| {ENDC} ")

    while sensors_on:  # global variable to stop loop
        try:
            local_temp, local_hum = sensor_cls.get_data()  # Read from local sensor
            time_now = datetime.now().strftime("%H:%M")    # Time of reading

            if local_temp == 0.0:
                bad_readings += 1
                reading_accepted = False
                if bad_readings == 3:
                    global_action = "sensors_off"
                    hvac_on = False
                    # raise SensorError
            else:
                reading_accepted = True
                bad_readings = 0
        except TypeError:
            print(f"{FAIL} [ERROR]: Received weird data{ENDC} ")
  
        
        action = hvacLogic.get_action([LOCAL_SENSOR_PRIORITY, CURRENT_SP, local_temp, local_hum])
        if reading_accepted and hvac_on and action:
            action_q.put({'local': action})

        if exit_event.is_set():
            break

        sleep(SENSOR_DELAY)

    print(f"{WARN} |*** Stopping Sensor Thread ***| {ENDC} ")


@app.route("/")
@app.route("/thermostat", methods=['POST', 'GET'])
@app.route("/thermostat/<action>", methods=['POST', 'GET'])
def thermostat(action='on'):
    """THERMOSTAT PAGE
    """
    global global_action 

    global_action = f"{action}"  # dynamic url used to turn on or off
    return render_template('hub/thermostat.html', title=" - Thermostat", sp=CURRENT_SP)


@app.route("/schedules", methods=['POST', 'GET'])
def schedules():

    if request.method == "POST":
        global HOME_AWAY, SETPOINTS
        
        HOME_AWAY[0] = request.form["awake-display"].strip(' ')
        HOME_AWAY[1] = request.form["sleep-display"].strip(' ')
        config.set('HVAC', 'awake_time', HOME_AWAY[0])
        config.set('HVAC', 'sleep_time', HOME_AWAY[1])

        with open('saved_config.ini', 'w') as f:
            config.write(f)

    return render_template("hub/schedules.html", title=" - Schedules")


@app.route("/rooms", methods=['POST', 'GET'])
def rooms():
    if request.method == "POST":
        NEW_ROOM = request.form["room_name"]
        NEW_MAC = request.form["mac_addr"]
        NEW_PRIORITY = request.form["priority"]

        print(NEW_ROOM, NEW_MAC, NEW_PRIORITY)

    return render_template("hub/rooms.html", title=" - Rooms")


@app.route("/settings", methods=['POST', 'GET'])
@app.route("/settings/<page>", methods=['POST', 'GET'])
def settings(page=None):
    """SETTINGS PAGE
    """
    global BACKGROUND_TYPE, BACKGROUND_POS, INTERFACE_THEME, INTERFACE_UNITS, BACKGROUND_COLOR, BACKGROUND_FILE, WEATHER_LOCATION, weatherAPI, RESULT_LIST, LOCATION

    if request.method == "POST":
        BACKGROUND_TYPE = request.form["image-type"]
        BACKGROUND_POS = request.form["image-position"]
        INTERFACE_THEME = request.form["interface-theme"]
        INTERFACE_UNITS = request.form["interface-unit"]
        BACKGROUND_COLOR = request.form["color-chooser"]

        if request.form["file-chooser"] != '':
            BACKGROUND_FILE = request.form["file-chooser"]

        WEATHER_LOCATION = request.form["location-search"]

        if WEATHER_LOCATION != '':  # If the user entered a new location, search all possibilities
            RESULT_LIST = weatherAPI.search_locations(WEATHER_LOCATION)
            WEATHER_LOCATION = ''
        else:
            RESULT_LIST = []

        # Write to Config File
        if "search-results" in request.form:  # After submitting the search the form now contains a list of options from which they choose
            LOCATION = request.form["search-results"]
            config.set('WEATHER', 'location', LOCATION)
        config.set('APP', 'background-type', BACKGROUND_TYPE)
        config.set('APP', 'background-position', BACKGROUND_POS)
        config.set('APP', 'background-color', BACKGROUND_COLOR)
        if BACKGROUND_FILE != "":
            config.set('APP', 'background-file', BACKGROUND_FILE)
        config.set('APP', 'interface-color', INTERFACE_THEME)
        config.set('WEATHER', 'units', INTERFACE_UNITS)

        with open('saved_config.ini', 'w') as f:
                    config.write(f)
        
    # RETURN THE SELECTED SETTING PAGE
    if page:
        return render_template(f"hub/settings/{page}.html")
    else:
        return render_template("hub/settings.html", title=" - Settings")


@app.route('/_load_bt_sensors', methods=['POST'])
def load_bt_sensors():

    return jsonify(SAVED_BT_SENSORS)

@app.route('/_update_rooms', methods=['POST'])
def update_rooms():
    global display_q, bt_dict, local_temp, local_hum, LOCAL_SENSOR_PRIORITY

    while not display_q.empty():
        data_list = display_q.get_nowait()
        bt_dict[data_list[0]] = [ data_list[1], data_list[2] ]

    bt_dict['local_values'] = [ local_temp, local_hum, LOCAL_SENSOR_PRIORITY ]

    return jsonify(bt_dict)

@app.route('/_update_thermostat', methods=['POST'])
def update_sensor_data():
    """Request route for sensor and time data
    """
    global local_temp, local_hum, time_now, sensor_data

    d = datetime.strptime(time_now, "%H:%M")
    if MINI_GUI:
        sensor_data.put([local_temp, local_hum])  # send local sensor data to MiniGUI

    return jsonify({
        'temperature': str(local_temp) + ' &#176;',
        'humidity': str(local_hum) + ' %',
        'time_now': d.strftime("%-I:%M %p"),
    })


@app.route('/_mode_changed', methods=["POST"])  # Route used to convey UI data to the HVAC Control Loop
def _mode_changed():
    global MODE, global_action, hvacControl, hvac_on, sensors_on, config, hvacThread

    if request.method == "POST":
        try:
            new_mode = str(request.data, "utf-8")

            if MODE == 'off' and new_mode != MODE:  # Turn back on from an off position
                print(f"{MSGS} Reloading... {ENDC} ")
                MODE = new_mode
                hvac_on = True
                hvacControl.mode_change(MODE)

                if not hvacThread.is_alive():
                    hvacThread = Thread(target=_hvac_control)  # Restart the Thread
                    hvacThread.start()

                config.set('HVAC', 'mode', MODE)

                with open('saved_config.ini', 'w') as f:
                    config.write(f)

                return redirect(url_for('thermostat', action='on'))

            elif new_mode != MODE:
                MODE = new_mode
                print(f"{MSGS} [MODE CHANGE]: {MODE} {ENDC} ")
                config.set('HVAC', 'mode', MODE)

                with open('saved_config.ini', 'w') as f:
                    config.write(f)

                if MODE == 'off':
                    hvac_on = False
                    hvacControl.mode_change(MODE)
                    global_action = 'hvac_off'
                else:
                    hvacControl.mode_change(MODE)
                    # hvacControl.relay_control(local_temp, local_hum, MODE)
                    global_action = 'on'

                return "MODE changed"

            else:
                return "MODE not changed"

        except Exception:
            print(f"{FAIL} [ERROR]: {ENDC} ")
            return "[ERROR]: in 'def mode_changed():'"


@app.route('/_sp_changed', methods=["POST"])  # Route used to convey UI data to the HVAC Control Loop
def _sp_changed():
    global SETPOINTS, HOME_AWAY, CURRENT_SP, local_temp, local_hum, MODE, hvac_on, config, setpoint_q
    
    if request.method == "POST":
        
        try:  # success means were on the Schedules page with 3 Setpoint selectors
            SETPOINTS[1] = float(request.form["away_temp"])
            SETPOINTS[2] = float(request.form["sleep_temp"])
            SETPOINTS[0] = float(request.form["home_temp"])
            config.set('HVAC', 'setpoints', str(SETPOINTS))

            with open('saved_config.ini', 'w') as f:
                config.write(f)

            # Get CURRENT_SP to send to the bt_listener setpoint_q
            index = hvacControl.get_home_awake(HOME_AWAY, get=True)
            CURRENT_SP = SETPOINTS[index]
            old = setpoint_q.get_nowait()
            print(f"{MSGS} OLD: {old}, NEW: {CURRENT_SP} {ENDC}")
            setpoint_q.put(CURRENT_SP)

            hvacControl.sp_change( SETPOINTS, HOME_AWAY )  # Send to HVAC Object
            # hvacControl.relay_control(local_temp, local_hum, MODE)  # Hmmmmmmmmmmm, logic needs to change

            return "setpoints changed"
        
        except KeyError:  # This means were on the Thermostat page with a single slider reflecting the setpoint ATM [home, sleep, away]
            new_sp = float(request.form["current_temp_sp"])
            if new_sp != CURRENT_SP and hvac_on:
                CURRENT_SP = new_sp
                index = hvacControl.get_home_awake(HOME_AWAY, get=True)
                # Get CURRENT_SP to send to the bt_listener setpoint_q
                old = setpoint_q.get_nowait()
                print(f"{MSGS} OLD: {old}, NEW: {CURRENT_SP} {ENDC}")
                setpoint_q.put(CURRENT_SP)

                SETPOINTS[index] = CURRENT_SP
                config.set('HVAC', 'setpoints', str(SETPOINTS))

                with open('saved_config.ini', 'w') as f:
                    config.write(f)

                hvacControl.sp_change( SETPOINTS, HOME_AWAY )
                # hvacControl.relay_control(local_temp, local_hum, MODE)

            return "setpoint changed"

        except ValueError:
            print(f"{FAIL} [ERROR]: in 'def sp_changed()'{ENDC} ")

            return "[ERROR]: in 'def sp_changed()'"
    else:
        return None


@app.route('/_get_config', methods=['POST'])
def _get_config():
    """"""
    global MODE, SETPOINTS, HOME_AWAY, BACKGROUND_TYPE, BACKGROUND_POS, INTERFACE_THEME, INTERFACE_UNITS, BACKGROUND_COLOR, BACKGROUND_FILE

    return jsonify({
        'hvac_mode': MODE,
        'home_setpoint': SETPOINTS[0],
        'away_setpoint': SETPOINTS[1],
        'sleep_setpoint': SETPOINTS[2],
        'awake-time': HOME_AWAY[0],
        'sleep-time': HOME_AWAY[1], 
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
    global sensors_on, local_temp, local_hum, time_now, exit_event, FlaskServer, ThreadList

    def update_data():
        print(f"{START} |*** Start of Chart GENERATOR ***| {ENDC} ")

        while sensors_on:  # global variable to stop loop
            d = datetime.strptime(time_now, "%H:%M")
            json_data = json.dumps(
                {'time': d.strftime("%-I:%M %p"), 'temp': float(local_temp), 'hum': float(local_hum), 'refresh': 'false'})
            yield f"data:{json_data}\n\n"

            if exit_event.is_set():
                for thread in ThreadList:
                    thread.join()
                print(f"{WARN} |*** Stopping Chart Generator ***| {ENDC} ")
                break
            sleep(60)

    return Response(update_data(), mimetype='text/event-stream')


@app.route('/_update_weather', methods=['POST', 'GET'])
def _update_weather():
    global weatherAPI, LOCATION, INTERFACE_UNITS
    weather_dict = {}
    weather_dict = weatherAPI.update_owm(INTERFACE_UNITS, LOCATION)
    return jsonify(weather_dict)


""" MAIN RUN SECTION
"""
if __name__ == '__main__':

    if MODE == "off":
        global_action = "hvac_off"
        if hvac_on:
            hvac_on = False  # it should stop thread
            print(f"{MSGS} HVAC is now off {ENDC} ")
        else:
            print(f"{WARN} HVAC not running {ENDC} ")
        if not sensors_on:
            sensors_on = True
            sensors = Thread(target=_check_sensors)  # Loops every 1 second (Sensor, Chart & Clock update)
            ThreadList.append(sensors)
        else:
            print(f"{WARN} Sensors already running {ENDC} ")
        if bt_on:
            bt_on = False  # it should stop thread
            bt_listener.bt_toggle(False)
            bt_manager.bt_toggle(False)
            print(f"{MSGS} BT is now off {ENDC} ")
        else:
            print(f"{WARN} BT not running {ENDC} ")

    elif global_action == 'on':
        if not sensors_on:
            sensors_on = True
            sensors = Thread(target=_check_sensors)  # Loops every 1 second (Sensor, Chart & Clock update)
            ThreadList.append(sensors)
        else:
            print(f"{WARN} Sensors already on {ENDC} ")
        if not hvac_on:
            hvac_on = True
            hvacThread = Thread(target=_hvac_control)  # Loops every 10 minutes (Relay Control)
            ThreadList.append(hvacThread)
        else:
            print(f"{WARN} HVAC already on {ENDC} ")
        if not bt_on and (SAVED_BT_SENSORS != {}):
            bt_on = True  # it starts thread
            bt_listener.bt_toggle(True)
            bt_manager.bt_toggle(True)
            bt_manage = Process(target=bt_manager.connect_all)
            ProcessList.append(bt_manage)
            setpoint_q.put(CURRENT_SP)
            # sp = setpoint_q.get()
            # print(sp)
            # setpoint_q.put(sp)
            bt_listen = Process(target=bt_listener.check_bt_sensors, args=(bt_sensor_data, action_q, setpoint_q, display_q))
            ProcessList.append(bt_listen)
        elif SAVED_BT_SENSORS == {}:
            print("NO BLUETOOTH DEVICES SAVED")
        else:
            print(f"{WARN} BT already on {ENDC} ")

    elif global_action == 'sensors_off':
        if sensors_on:
            sensors_on = False  # it should stop thread
            print(f"{MSGS} Sensors are now off {ENDC} ")
        else:
            print(f"{WARN} [WARNING] Sensors not running {ENDC} ")
        if bt_on:
            bt_on = False  # it should stop thread
            bt_listener.bt_toggle(False)
            bt_manager.bt_toggle(False)
            print(f"{MSGS} BT is now off {ENDC} ")
        else:
            print(f"{WARN} BT not running {ENDC} ")

    else:
        print(f"{WARN} [WARNING] MODE error {ENDC} ")

    """ Support GUI for the 3" TFT touchscreen for SBC's ( GUIZERO [...for now] ) """
    if MINI_GUI == 'True':
        small_gui = Thread( target=GUI, 
                args=(sensor_data, exit_event)
                )        
        ThreadList.append(small_gui)

    """ Start ALL THE PROCESSES:
    - BT Manager
    - BT Listener
    - Flask Server
    """ 
    for process in ProcessList:
        process.start()

    """ Start ALL THE THREADS:
        - Local Sensor Thread
        - HVAC Control Thread
        - [OPTIONAL] Mini GUI for 3in TFT Thread
    """ 
    for thread in ThreadList:
        thread.start()

    FlaskServer = Process(target=app.run(host=HOST_IP,  # "open.sht",
                                         port=WEB_PORT,
                                         debug=False,
                                         threaded=True))
    FlaskServer.start()

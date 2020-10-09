from modules.thermostat import HvacLogic

hvac = HvacLogic()

class BTListener():
    """PROCESS: Runs as often as neccesary to keep the data queue empty
        :returns [ priority, temp, hum ]
    """

    def __init__(self, bt_on, device_dict):
        global hvac

        self.temperature = 0.0
        self.humidity = 0.0
        self.current_sp = 0.0
        self.bt_on = bt_on
        self.devices = device_dict

    def bt_toggle(self, on_off):
        self.bt_on = on_off

    def new_device(self, new_device):
        # Format: [ "NAME", [ "MAC_ADDR", "PRIORITY" ] ]
        self.devices[new_device[0]] = new_device[1]

    def check_bt_sensors(self, bt_data_q, action_q, setpoint_q, display_q):
        self.bt_data_q = bt_data_q
        self.action_q = action_q
        self.display_q = display_q

        while self.bt_on:
            try:
                self.current_sp = setpoint_q.get_nowait()
                setpoint_q.put(self.current_sp)
                # print(f"SETPOINT: {self.current_sp}")
            except:
                pass

            try:
                reading = self.bt_data_q.get(block=True, timeout=2)
                
                for key in self.devices.keys():
                    if key in reading.keys():
                        self.temperature = float(reading[key][0])
                        self.humidity = float(reading[key][1].strip('/r'))
                        action = hvac.get_action([int(self.devices[key][1]), self.current_sp, self.temperature, self.humidity])
                        send = {str(key): action}
                        self.action_q.put(send)
                        self.display_q.put([key, self.temperature, self.humidity])

            except KeyboardInterrupt:
                print("Closing Connections")
                break
            
            except Exception as e:
                print(e)
                pass

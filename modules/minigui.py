# class MiniGui():

def mini_gui(sensor_queue, close_event):
    from guizero import App, Window, Box, Text, PushButton, Slider
    from queue import Queue
    from time import sleep

    sensor_info = sensor_queue
    current_temp = "0.0"
    current_hum = "0.0"

    BACKGROUND = "#333333"
    TEXT = "#fafafa"
    DATA_BOX_HEIGHT = str( 320 * 0.3 ) + "px"
    TEMP_COLOR = "#E91E63"
    HUM_COLOR = "#00C6E1"
    # NAV_BUTT_X = 15
    NAV_BUTT_y = 1
    BTN_X = 20
    BTN_Y = 1

    print(close_event)

    def data_listener():
        data_list = sensor_info.get()
        temp_show.value = str(data_list[0])
        hum_show.value = str(data_list[1])

    def exit_listener():
        if close_event.is_set():
            app.destroy()

    def exit_app():
        close_event.set()
            
    def slider_move(slider_value):
        sp_show.value = str(float(slider_value) / 2) + "C"

    def do_nothing():
        print("Button was pressed")


    app = App(bg=BACKGROUND, width=480, height=320)  #, layout="grid"
    app.text_color = TEXT
    app.repeat(1000, exit_listener)
    app.on_close(exit_app)

    #  NAVBAR SECTION
    nav_box = Box(app, align="top", width="fill", height="30px")
    thermostat_page = PushButton(nav_box, align="left", command=do_nothing, padx=10, pady=10, width="fill", height=NAV_BUTT_y, text="Thermostat")
    schedule_page = PushButton(nav_box, align="left", command=do_nothing, padx=10, pady=10, width="fill", height=NAV_BUTT_y, text="Schedules")
    room_page = PushButton(nav_box, align="left", command=do_nothing, padx=10, pady=10, width="fill", height=NAV_BUTT_y, text="Rooms")

    #  SENSOR DATA SECTION
    spacer_top1 = Box(app, align="top", height="5px")
    data_box = Box(app, align="top", width="fill", height=DATA_BOX_HEIGHT, border=True)
    spacer_left1 = Box(data_box, align="left", width="20px")
    spacer_right1 = Box(data_box, align="right", width="20px")

    temp_show = Text(data_box, align="left", text=current_temp,size=36, color=TEMP_COLOR, font="Orbitron")
    temp_show.repeat(2000, data_listener)
    hum_show = Text(data_box, align="right", text=current_hum,size=36, color=HUM_COLOR, font="Orbitron")

    #  BUTTON SECTION:
    spacer_top2 = Box(app, align="top", height="15px")
    btn_box = Box(app, align="top", width="fill", height="fill", border=True)
    spacer_left2 = Box(btn_box, align="left", width="20px")
    spacer_right2 = Box(btn_box, align="right", width="20px")

    top_btns = Box(btn_box, align="top")
    auto = PushButton(top_btns, align="left", width=BTN_X, height=BTN_Y, text="Auto")
    spacer_left3 = Box(top_btns, align="left", width="5px")
    cool = PushButton(top_btns, align="right", width=BTN_X, height=BTN_Y, text="Cool")

    spacer_mid1 = Box(btn_box, align="top", height="5px")

    bottom_btns = Box(btn_box, align="top")
    heat = PushButton(bottom_btns, align="left", width=BTN_X, height=BTN_Y, text="Heat")
    spacer_left4 = Box(bottom_btns, align="left", width="5px")
    off = PushButton(bottom_btns, align="right", width=BTN_X, height=BTN_Y, text="System Off")

    #  SLIDER: 
    spacer_top3 = Box(app, align="top", height="8px")
    slider_box = Box(app, align="top", width="fill", height="fill")
    spacer_left2 = Box(slider_box, align="left", width="20px")
    spacer_right2 = Box(slider_box, align="right", width="20px")
    temp_slider = Slider(slider_box, align="left", width="fill", start=30, end=60, command=slider_move)
    temp_slider.text_color = BACKGROUND
    sp_show = Text(slider_box, align="right", width=7, size=24, font="Orbitron", color=TEXT, text=(str(float(temp_slider.value) / 2) ) + "C")
    spacer_top3 = Box(app, align="top", height="8px")

    """  SCHEDULES WINDOW  """
    # window = Window(app, bg="#333333", width=480, height=320)
    # button = PushButton(app, command=do_nothing)


    app.display()
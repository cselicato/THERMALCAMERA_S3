"""
    Test to plot the received area temperature
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
from datetime import datetime
import paho.mqtt.client as mqtt
import re

from THERMALCAMERA_S3.videomaker import VideoMaker

MQTT_SERVER = "test.mosquitto.org"
MQTT_PATH = "/singlecameras/camera1/area/#"

video = VideoMaker("area", size=(960, 720))

t, avg_T, max_T, min_T = [], [], [], []

start_time = datetime.now()

fig, ax = plt.subplots()
sc_avg, = ax.plot([], [], color='green', markersize=12, label="Average T")
sc_max, = ax.plot([], [], color='red', markersize=12, label="Max T")
sc_min, = ax.plot([], [], color='blue', markersize=12, label="Min T")
fig.set_size_inches(5, 4)

ax.set_xlabel("Time from start [s]")
ax.set_ylabel("T [°C]")
ax.set_xlim(0, 10)
ax.set_ylim(20, 30)
ax.grid()
ax.legend()
fig_text = fig.figure.text(0.55, 0.9, "Waiting for data...")

def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected with result code:", reason_code)
    client.subscribe(MQTT_PATH)

def on_message(client, userdata, msg):

    if msg.topic == "/singlecameras/camera1/area/current":
        if msg.payload.decode() == "none":
            print("Currently no area is defined.\n")

    if msg.topic == "/singlecameras/camera1/area/data":
        # Data is received as:  max: 31.81 min: 26.04 avg: 29.74 x: 0 y: 14 w: 5 h: 5
        rc = list(map(str, msg.payload.decode().split(',')))
        # print(rc)
        st = msg.payload.decode()
        pattern = r"(\w+):\s*([\d.]+)"
        matches = re.findall(pattern, st)

        # Convert to dictionary, converting numbers to float or int automatically
        data = {k: float(v) if '.' in v else int(v) for k, v in matches}

        fig_text.set_text(f"Showing ({int(data.get("x"))}, {int(data.get("y"))}), w={int(data.get("w"))} h={int(data.get("h"))}")

        x = (datetime.now() - start_time).total_seconds()
        t.append(x)
        avg_T.append(data.get("avg"))
        min_T.append(data.get("min"))
        max_T.append(data.get("max"))

        # plot has to be updated in the callback (so when data is received)
        sc_avg.set_data(t, avg_T)
        sc_min.set_data(t, min_T)
        sc_max.set_data(t, max_T)

        if x >= ax.get_xlim()[1]:
            ax.set_xlim(0, x + 10)

        ymin, ymax = ax.get_ylim()
        new_min = min(min(avg_T), min(min_T), min(max_T))
        new_max = max(max(avg_T), max(min_T), max(max_T))

        pad = 0.1 * (new_max - new_min if new_max != new_min else 1)
        new_min -= pad
        new_max += pad

        if new_min < ymin or new_max > ymax:
            ax.set_ylim(new_min, new_max)

        ax.figure.canvas.draw()
        video.add_frame(fig)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_SERVER, 1883, 60)

client.loop_start()

video_button = CheckButtons(plt.axes([0.1, 0.9, 0.3, 0.075]), ['Video',], [False,],
                          check_props={'color':'green', 'linewidth':1})

def video_button_cb(label):

    global video
    if not video.filming:
        # when checkbox is clicked and previously the video was not being saved,
        # start video
        video.start_video()
    else:
        # if video was being taken, stop and save the file
        video.stop_video()

video_button.on_clicked(video_button_cb)

plt.show(block=True)
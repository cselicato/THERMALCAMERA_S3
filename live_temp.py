"""
    Test to plot the received pixel temperature
"""

from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
import paho.mqtt.client as mqtt

from THERMALCAMERA_S3.videomaker import VideoMaker

MQTT_SERVER = "test.mosquitto.org"
MQTT_PATH = "/singlecameras/camera1/pixels/#"

video = VideoMaker("pixel", size=(960, 720))

xdata, ydata = [], []
start_time = datetime.now()

fig, ax = plt.subplots()
fig.set_size_inches(5, 4)
scatter, = ax.plot([], [], color='red', markersize=12)
ax.set_xlabel("Time from start [s]")
ax.set_ylabel("T [°C]")
ax.set_xlim(0, 10)
ax.set_ylim(20, 30)
ax.grid()
fig_text = fig.figure.text(0.75, 0.9, "Waiting for data...")

def on_connect(client, userdata, flags, reason_code, properties):
    """
    Subsciribe to desired topic(s)

    Subscribing in on_connect() means that if we lose the connection and
    reconnect then subscriptions will be renewed.
    """

    print("Connected with result code:", reason_code)
    client.subscribe(MQTT_PATH)

def on_message(client, userdata, msg):
    """
    Define what happens when a MQTT message is received: if the topic is the pixel data
    it adds it to the plot, if it receives a message thet no pixels are currently
    defined it prints a message
    """

    if msg.topic == "/singlecameras/camera1/pixels/current":
        if msg.payload.decode() == "none":
            print("Currently no pixels are defined.\n")

    if msg.topic == "/singlecameras/camera1/pixels/data":
        # Data is received as: 2 25 30.77,19 18 23.87,11 9 23.22
        rc = list(map(str, msg.payload.decode().split(',')))
        # print(rc)

        current = np.empty((0, 3))
        for i, pixel in enumerate(rc):
            info = np.array(list(map(float, pixel.split(' '))))
            # print(info)
            current = np.append(current, [info], axis=0)

        # print(current)
        fig_text.set_text(f"Showing {int(current[0][0])}, {int(current[0][1])}")
        value = current[0][2]

        x = (datetime.now() - start_time).total_seconds()
        xdata.append(x)
        ydata.append(value)

        # plot has to be updated in the callback (so when data is received)
        scatter.set_data(xdata, ydata)

        if x >= ax.get_xlim()[1]:
            ax.set_xlim(0, x + 10)

        ymin, ymax = ax.get_ylim()
        new_min = min(ydata)
        new_max = max(ydata)

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
    """
    Relate check button state to start/stop of video  
    """

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

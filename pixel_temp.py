"""
    Test to plot the received pixel temperature
"""

from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
import paho.mqtt.client as mqtt
from loguru import logger

from THERMALCAMERA_S3.videomaker import VideoMaker

MQTT_SERVER = "test.mosquitto.org"
MQTT_PATH = "/singlecameras/camera1/pixels/#"

video = VideoMaker("pixel", size=(960, 720))

xdata, ydata = [], []
start_time = datetime.now()

fig, ax = plt.subplots()
plt.subplots_adjust(right=0.77)
fig.set_size_inches(5, 4)
scatter, = ax.plot([], [], color='red', markersize=12)
ax.set_xlabel("Time from start [s]")
ax.set_ylabel("T [°C]")
# ax.set_xlim(0, 10)
ax.grid()
fig_text = fig.figure.text(0.55, 0.9, "Waiting for data...")

pixels_data = {} # will contain the pixel as a key and as a value another dict
                 #  with the times, values and Line2D 

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
        try:
            msg = msg.payload.decode()
            # get current pixels and data from message
            current = [list(map(float, p.split(' '))) for p in msg.split(",")]
            t = (datetime.now() - start_time).total_seconds()
            # TODO: it would probably be more useful with the UTC time on the x axis

            # now update value in dictionary or add new one if not present
            for x, y, val in current:
                pixel = (int(x), int(y))
                if pixel not in pixels_data: # add to dict and make new line
                    logger.info(f"Receiving new pixel: {pixel}")
                    # create line for its data
                    l, = ax.plot([], [], label=str(pixel), color=np.random.rand(3,))
                    ax.legend(loc="upper left", bbox_to_anchor=(1,1))
                    # add (empty) data and Line2D to dict
                    pixels_data[pixel] = {"times": [], "temps": [], "line": l}
                # add values (temperature and time)
                single = pixels_data[pixel]
                single["times"].append(t)
                single["temps"].append(val)
                single["line"].set_data(single["times"], single["temps"])

            # (if needed) update plot axes
            if any(len(d["times"])>0 for d in pixels_data.values()):
                xmax = max(max([d["times"] for d in pixels_data.values()]))
                if xmax >= ax.get_xlim()[1]:
                    ax.set_xlim(0, xmax*1.25)

                ymin, ymax = ax.get_ylim()
                new_min = min(min([d["temps"] for d in pixels_data.values()]))
                new_max = max(max([d["temps"] for d in pixels_data.values()]))
                pad = 0.1 * (new_max - new_min if new_max != new_min else 1)
                new_min -= pad
                new_max += pad

                if new_min < ymin or new_max > ymax:
                    ax.set_ylim(new_min, new_max)

            fig_text.set_text(f"Number of current pixels: {len(current)}")
            ax.figure.canvas.draw()
            video.add_frame(fig)
        except ValueError:
            logger.warning(f"Received data has invalid format: {msg}")
            pass

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_SERVER, 1883, 60)

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

try:
    client.loop_start()
    plt.show()
except KeyboardInterrupt:
    plt.close("all")
    logger.info("Closed plot.")
finally:
    logger.info("Stopping loop and disconnecting...")
    client.loop_stop()
    client.disconnect()
    logger.info("Done, stopping script.")

"""
    Test to plot the received area temperature
"""

from datetime import datetime
import re
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
import paho.mqtt.client as mqtt
from loguru import logger

from THERMALCAMERA_S3.videomaker import VideoMaker

MQTT_SERVER = "test.mosquitto.org"
MQTT_PATH = "/singlecameras/camera1/area/#"

video = VideoMaker("area", size=(960, 720))

t, avg_T, max_T, min_T = [], [], [], []

start_time = datetime.now()

fig, ax = plt.subplots()
plt.subplots_adjust(right=0.77)
sc_avg, = ax.plot([], [], color='green', markersize=12, label=r"$T_{avg}$")
sc_max, = ax.plot([], [], color='red', markersize=12, label=r"$T_{max}$")
sc_min, = ax.plot([], [], color='blue', markersize=12, label=r"$T_{min}$")
fig.set_size_inches(5, 4)

ax.set_xlabel("Time from start [s]")
ax.set_ylabel("T [°C]")
ax.set_xlim(0, 10)
ax.grid()
ax.legend(loc="upper left", bbox_to_anchor=(1,1))
fig_text = fig.figure.text(0.55, 0.9, "Waiting for data...")

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
    Define what happens when a MQTT message is received: if the topic is the area data
    it adds it to the plot, if it receives a message thet no area is currently
    defined it prints a message
    """

    if msg.topic == "/singlecameras/camera1/area/current":
        if msg.payload.decode() == "none":
            print("Currently no area is defined.\n")

    if msg.topic == "/singlecameras/camera1/area/data":
        # Data is received as:  max: 31.81 min: 26.04 avg: 29.74 x: 0 y: 14 w: 5 h: 5
        try:
            st = msg.payload.decode()
            pattern = r'(\w+):\s(\d+\.?\d?)'
            matches = re.findall(pattern, st)
            # Convert to dictionary, converting numbers to float or int automatically
            data = {k: float(v) if "." in v else int(v) for k, v in matches}

            x, y, w, h = data["x"], data["y"], data["w"], data["h"]
            fig_text.set_text(f"Showing ({int(x)}, {int(y)}), w={int(w)} h={int(h)}")



            if (data["max"] and data["min"] and data["avg"]): # values should be appended only if they are all present
                x = (datetime.now() - start_time).total_seconds()
                avg_T.append(data["avg"]) # accessing the dictionary like this allows for KeyError
                min_T.append(data["min"])
                max_T.append(data["max"])
                t.append(x)
                # plot has to be updated in the callback (so when data is received)
                sc_avg.set_data(t, avg_T)
                sc_min.set_data(t, min_T)
                sc_max.set_data(t, max_T)

                if x >= ax.get_xlim()[1]:
                    ax.set_xlim(0, x + 10)

                ymin, ymax = ax.get_ylim()
                new_min = min(*avg_T, *min_T, *max_T)
                new_max = max(*avg_T, *min_T, *max_T)

                pad = 0.1 * (new_max - new_min if new_max != new_min else 1)
                new_min -= pad
                new_max += pad

                if new_min < ymin or new_max > ymax:
                    ax.set_ylim(new_min, new_max)

                ax.figure.canvas.draw()
                video.add_frame(fig)

        except (TypeError, KeyError):
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

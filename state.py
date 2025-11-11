# """
#     Receive data from a thermal camera MLX90640 connected to AtomS3 and display it
# """

# from datetime import datetime, timedelta
# import matplotlib.pyplot as plt
# import paho.mqtt.client as mqtt

# from THERMALCAMERA_S3.controlpanel import ControlPanel


# MQTT_SERVER = "test.mosquitto.org"
# MQTT_PATH = "/singlecameras/camera1/#"

# start_time = datetime.now()
# max_dead_time = timedelta(seconds=4) # in seconds
# last_received = datetime.now()-timedelta(seconds=10)


# def on_connect(client, userdata, flags, reason_code, properties):
#     client.subscribe(MQTT_PATH)

# # The callback for when a PUBLISH message is received from the server.
# def on_message(client, userdata, msg):
#     global last_received
#     last_received = datetime.now()
#     print("Received")

# client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
# client.on_connect = on_connect
# client.on_message = on_message
# client.connect(MQTT_SERVER, 1883, 60)

# panel = ControlPanel()

# # def update_status(last):
# if datetime.now()-last_received<max_dead_time:
#     print("on")
#     panel.state.set_text("ONLINE")
#     panel.state.set_color("green")
#     bbox = panel.state.get_bbox_patch()
#     bbox.set_facecolor((0.8, 1.0, 0.8))  # light green
#     bbox.set_edgecolor((0.5, 1.0, 0.5))  # green border
# else:
#     print("off")
#     panel.state.set_text("OFFLINE")
#     panel.state.set_color("red")
#     bbox = panel.state.get_bbox_patch()
#     bbox.set_facecolor((1.0, 0.8, 0.8))  # light red (soft pinkish fill)
#     bbox.set_edgecolor((1.0, 0.5, 0.5))  # red border


# try:
#     client.loop_start()
#     plt.show()
# except KeyboardInterrupt:
#     plt.close("all")
# finally:
#     client.loop_stop()
#     client.disconnect()
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
from THERMALCAMERA_S3.controlpanel import ControlPanel

MQTT_SERVER = "test.mosquitto.org"
MQTT_PATH = "/singlecameras/camera1/#"

max_dead_time = timedelta(seconds=2)
last_received = datetime.now() - timedelta(seconds=10)


# --- MQTT setup ---
def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe(MQTT_PATH)

def on_message(client, userdata, msg):
    global last_received
    last_received = datetime.now()
    print("Received MQTT message")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_SERVER, 1883, 60)
client.loop_start()


# --- Matplotlib UI setup ---
panel = ControlPanel()

def update_status():
    """Check last_received and update text & colors."""
    now = datetime.now()
    if now - last_received < max_dead_time:
        panel.state.set_text("ONLINE")
        panel.state.set_color("green")
        bbox = panel.state.get_bbox_patch()
        bbox.set_facecolor((0.8, 1.0, 0.8))
        bbox.set_edgecolor((0.5, 1.0, 0.5))
    else:
        panel.state.set_text("OFFLINE")
        panel.state.set_color("red")
        bbox = panel.state.get_bbox_patch()
        bbox.set_facecolor((1.0, 0.8, 0.8))
        bbox.set_edgecolor((1.0, 0.5, 0.5))

    # Redraw the panel
    panel.fig.canvas.draw()


# --- Timer: runs update_status() every 500 ms ---
timer = panel.fig.canvas.new_timer(interval=500)
timer.add_callback(update_status)
timer.start()

# --- Blocking GUI ---
try:
    plt.show()  # blocks until user closes window
finally:
    timer.stop()
    client.loop_stop()
    client.disconnect()

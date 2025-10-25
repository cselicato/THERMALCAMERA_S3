"""
    Receive data from a thermal camera MLX90640 conneced to AtomS3
"""

import struct
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from matplotlib.widgets import CheckButtons
import matplotlib.animation as animation
import cv2
import paho.mqtt.client as mqtt

MQTT_SERVER = "test.mosquitto.org"
MQTT_PATH = "/singlecameras/camera1/#"

# Initialize a list of float as per your data. Below is a random example
fig, ax = plt.subplots()
fig.set_size_inches(5,4)
im = ax.imshow(np.random.rand(24,32)*30+10, cmap='inferno')
plt.colorbar(im)
single_pixel = [0, 0]
area = [[0,0], [0,0]]
click_count = 0
draw_pixel, = ax.plot([], [], marker='+', color='red', markersize=12, linestyle='None')
draw_area, = ax.plot([], [], marker='+', color='blue', markersize=12, linestyle='None')

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_PATH)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global im
    global single_pixel

    if msg.topic == "/singlecameras/camera1/image":
        flo_arr = [struct.unpack('f', msg.payload[i:i+4])[0] for i in range(0, len(msg.payload), 4)]
        im.set_data(np.array(flo_arr).reshape(24,32))
        plt.draw()
        draw_pixel.set_data([single_pixel[0]], [single_pixel[1]])
        if click_count==2:
            draw_area.set_data([area[0][0],area[1][0]], [area[0][1],area[1][1]])


    elif msg.topic == "/singlecameras/camera1/which_pixel":
        # get single pixel coordinates
        received = msg.payload.decode()
        single_pixel = list(map(int, received.split(' ')))


#    img = cv2.imread('img.png')
#    resized_img = cv2.resize(img, (320,240))
#    cv2.imwrite('img.png', resized_img)

# The callback for when the client receives a CONNACK response from the server.

# get the pixel coordinates from mouse click
def on_click(event):
    global click_count
    global area

    if not event.inaxes == ax:
        # when the click is outside of the axes do nothing
        return
    x = np.floor(event.xdata).astype(int)
    y = np.floor(event.ydata).astype(int)

    if not check_box.get_status()[0]:
        # if button is not clicked get point coordinates
        client.publish("/singlecameras/camera1/which_pixel", f"{x} {y}")
    else:
        # if clicked define area (two clicks are needed)
        if click_count>1:
            print("Resetting interesting area, click again")
            area = [[0,0], [0,0]]
            click_count = 0
            return
        area[click_count] = [x,y]
        click_count += 1

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_SERVER, 1883, 60)

client.loop_start()
cid = fig.canvas.mpl_connect('button_press_event', on_click)
cursor = Cursor(ax, useblit=True, color='black', linewidth=1 )

check_box = CheckButtons(plt.axes([0.3, 0.05, 0.3, 0.075]), ['Select area',], [False,], check_props={'color':'red', 'linewidth':1})
plt.show()

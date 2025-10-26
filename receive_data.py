"""
    Receive data from a thermal camera MLX90640 conneced to AtomS3
"""

import struct
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from matplotlib.widgets import CheckButtons
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

size = (960,720)
fps = 4
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video = cv2.VideoWriter('test_logic.mp4', fourcc, fps, size, isColor=True)
save_video = False
filming = False

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_PATH)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global im
    global single_pixel
    global save_video, filming

    if msg.topic == "/singlecameras/camera1/image":
        flo_arr = [struct.unpack('f', msg.payload[i:i+4])[0] for i in range(0, len(msg.payload), 4)]
        im.set_data(np.array(flo_arr).reshape(24,32))
        fig.canvas.draw() # draw canvas
        draw_pixel.set_data([single_pixel[0]], [single_pixel[1]])
        if click_count==2:
            draw_area.set_data([area[0][0],area[1][0]], [area[0][1],area[1][1]])

        if save_video:
            img = np.asarray(fig.canvas.renderer.buffer_rgba()) # get image from canvas as an array
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR) # Convert from RGBA to BGR (opencv's default)
            img = cv2.resize(img, size) # resize image to video size 
            video.write(img) # add image to video writer
        
        if (not save_video) and filming:
            video.release()
            print("Saved output video")
            filming = False


    if msg.topic == "/singlecameras/camera1/which_pixel":
        # get single pixel coordinates
        received = msg.payload.decode()
        single_pixel = list(map(int, received.split(' ')))

    if msg.topic == "/singlecameras/camera1/take_video":
        if msg.payload.decode() == "1":
            save_video = True
            filming = True
        else:
            save_video = False

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
        # if button is on define area (two clicks are needed)
        if click_count>1:   # reset area with more than two clicks
            print("Resetting interesting area, click again")
            area = [[0,0], [0,0]]
            click_count = 0
            return
        area[click_count] = [x,y]
        if click_count == 1:
            # do something with the selected area
            client.publish("/singlecameras/camera1/which_area", f"{area[0][0]} {area[0][1]} {area[1][0]} {area[1][1]}")
            print(f"The selected area is ({area[0][0]}, {area[0][1]}), ({area[1][0]}, {area[1][1]})")        
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

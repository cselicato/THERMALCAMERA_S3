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
single_pixels = np.empty((0, 2), dtype=int)     # this will contain the coordinates of the interesting pixels
area = [[0,0], [0,0]]
click_count = 0     # TODO: change name (misleading) (it should be clear that it's for the definition of the area)
draw_pixel, = ax.plot([], [], marker='+', color='red', markersize=12, linestyle='None')
draw_area, = ax.plot([], [], marker='+', color='blue', markersize=12, linestyle='None')

size = (960,720)
fps = 4
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
# TODO: check if more than one video can be saved
video = cv2.VideoWriter('test.mp4', fourcc, fps, size, isColor=True)
filming = False

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_PATH)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global im
    global single_pixels
    global filming

    # an image is recieved from the sensor: plot the image and, if video button is clicked, take video
    if msg.topic == "/singlecameras/camera1/image":
        flo_arr = [struct.unpack('f', msg.payload[i:i+4])[0] for i in range(0, len(msg.payload), 4)]
        im.set_data(np.array(flo_arr).reshape(24,32))
        fig.canvas.draw() # draw canvas
        draw_pixel.set_data(single_pixels[:,0],single_pixels[:,1])
        if click_count==2:
            draw_area.set_data([area[0][0],area[1][0]], [area[0][1],area[1][1]])

        if film_video.get_status()[0]:  # if video button on image is clicked, save frames
            filming = True
            img = np.asarray(fig.canvas.renderer.buffer_rgba()) # get image from canvas as an array
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR) # Convert from RGBA to BGR (opencv's default)
            img = cv2.resize(img, size) # resize image to video size 
            video.write(img) # add image to video writer
        
        if (not film_video.get_status()[0]) and filming:
            video.release()
            print("Saved output video")
            filming = False

# Defines what to do when  there is a mouse click on the figure:
# if area button is not clicked, get point and publish it
# if it is clicked define area (only one area at the time)
def on_click(event):
    global click_count
    global area
    global single_pixels

    if not event.inaxes == ax:
        # when the click is outside of the axes do nothing
        return
    
    # get coordinates of the mouse click
    x = np.floor(event.xdata).astype(int)
    y = np.floor(event.ydata).astype(int)

    if not select_area.get_status()[0]:
        # if area button is not clicked get point coordinates and publish them
        single_pixels = np.append(single_pixels, [(x, y)], axis=0)  # append pixel to array

        client.publish("/singlecameras/camera1/single_pixels/coord", f"{x} {y}")   # publish pixel position
    else:
        # if area button is clicked define area (two clicks are needed)
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

select_area = CheckButtons(plt.axes([0.45, 0.9, 0.3, 0.075]), ['Select area',], [False,], check_props={'color':'red', 'linewidth':1})
film_video = CheckButtons(plt.axes([0.1, 0.9, 0.3, 0.075]), ['Video',], [False,], check_props={'color':'green', 'linewidth':1})
plt.show()

"""
    Receive data from a thermal camera MLX90640 conneced to AtomS3
"""

import struct
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from matplotlib.widgets import CheckButtons
import matplotlib.patches as patches
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
area = np.empty((0, 4))
clicks = np.empty((0, 2), dtype=int)
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
    global single_pixels, area
    global filming

    # an image is recieved from the sensor: plot the image and, if video button is clicked, take video
    if msg.topic == "/singlecameras/camera1/image":
        flo_arr = [struct.unpack('f', msg.payload[i:i+4])[0] for i in range(0, len(msg.payload), 4)]
        im.set_data(np.array(flo_arr).reshape(24,32))
        fig.canvas.draw() # draw canvas
        draw_pixel.set_data(single_pixels[:,0],single_pixels[:,1]) # draw selected pixels on image
        if click_count==2:
            # draw_area.set_data([area[0][0],area[1][0]], [area[0][1],area[1][1]])
            # get lower left point
            # xy = np.empty((0, 2), dtype=int) 
            xy = (area[0][0],area[0][1])

            # get width and height
            w = area[0][2]
            h = area[0][3]

            # Create a Rectangle patch
            rect = patches.Rectangle(xy, w, h, linewidth=1, edgecolor='b', facecolor='none')

            # Add the patch to the Axes
            ax.add_patch(rect)

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

    if msg.topic == "/singlecameras/camera1/pixels/data":
        test = list(map(str, msg.payload.decode().split(',')))
        print("Recieved: ", msg.payload.decode())
        print("Lenght: ", len(test))

    if msg.topic == "/singlecameras/camera1/pixels/current":
        # get pixels the camera is already looking at
        if msg.payload.decode() != "none":
            current = list(map(str, msg.payload.decode().split(',')))
            # add each pixel to single_pixels
            for i in range(0, len(current)):
                coord = list(map(int, current[i].split(' ')))
                single_pixels = np.append(single_pixels, [coord], axis=0)

    if msg.topic == "/singlecameras/camera1/area/data":
        print("Area data: ", msg.payload.decode())
        
    if msg.topic == "/singlecameras/camera1/area/current":
        # get area the camera is already looking at
        if msg.payload.decode() != "none":
            area = np.empty((0, 4), dtype=int)  # forget previous area information
            area = np.append(area, [list(map(int, msg.payload.decode().split(' ')))], axis=0)


# Defines what to do when  there is a mouse click on the figure:
# if area button is not clicked, get point and publish it
# if it is clicked define area (only one area at the time)
def on_click(event):
    global click_count
    global area, clicks
    global single_pixels

    if not event.inaxes == ax:
        # when the click is outside of the axes do nothing
        return
    
    # get coordinates of the mouse click
    x = np.floor(event.xdata).astype(int)
    y = np.floor(event.ydata).astype(int)

    if select_area.get_status()[0]:
        # if area button is clicked define area (two clicks are needed)
        if click_count>1:   # reset area with more than two clicks
            print("Resetting interesting area, click again")
            area = np.empty((0, 4), dtype=int)
            clicks = np.empty((0, 2), dtype=int)
            click_count = 0
            [p.remove() for p in reversed(ax.patches)] # remove drawing of previous area
            return
        clicks = np.append(clicks, [(x, y)], axis=0)
        # area = np.append(area, [(x, y)], axis=0)
        draw_area.set_data(clicks[:,0],clicks[:,1])
        if click_count == 1:
            # publish the selected area
            x_left = int(np.min(clicks, axis=0)[0])
            y_low = int(np.min(clicks, axis=0)[1])
            w = int(abs(clicks[0][0] - clicks[1][0]))
            h = int(abs(clicks[0][1] - clicks[1][1]))
            area = np.append(area, [(x_left, y_low, w, h)], axis=0)
            client.publish("/singlecameras/camera1/area", f"{x_left} {y_low} {w} {h}")
            print(f"The selected area is ({clicks[0][0]}, {clicks[0][1]}), ({clicks[1][0]}, {clicks[1][1]})")        
        click_count += 1
    else:
        # if area button is not clicked get point coordinates and publish them
        single_pixels = np.append(single_pixels, [(x, y)], axis=0)  # append pixel to array
        # TODO: if coordinates are already present, do not append them
        client.publish("/singlecameras/camera1/pixels/coord", f"{x} {y}")   # publish pixel position
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

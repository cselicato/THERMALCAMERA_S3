"""
    Receive data from a thermal camera MLX90640 connected to AtomS3 and display it
"""

import struct
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from matplotlib.widgets import CheckButtons
from matplotlib import patches
import cv2
import paho.mqtt.client as mqtt

from THERMALCAMERA_S3.videomaker import VideoMaker
from THERMALCAMERA_S3.stuff import InterestingArea
from THERMALCAMERA_S3.stuff import InterestingPixels


MQTT_SERVER = "test.mosquitto.org"
MQTT_PATH = "/singlecameras/camera1/#"

# Initialize a list of float as per your data. Below is a random example
fig, ax = plt.subplots()
fig.set_size_inches(4,5)
im = ax.imshow(np.random.rand(32,24)*30+10, cmap='inferno')

fig_text = fig.figure.text(0.05, 0.05, "Waiting for thermal image...")
# create colorbar
cbar = plt.colorbar(im)
cbar_ticks = np.linspace(10., 40., num=7, endpoint=True)
cbar.set_ticks(cbar_ticks)
cbar.minorticks_on()

clicks = np.empty((0, 2), dtype=int)

draw_pixel, = ax.plot([], [], marker='+', color='red', markersize=12, linestyle='None')
draw_clicks, = ax.plot([], [], marker='+', color='blue', markersize=12, linestyle='None')

received = 0    # counter for how many thermal images have been received

video = VideoMaker()

area = InterestingArea()
single_pixels = InterestingPixels()

def update_cbar(colorbar, min, max):
    """
    Update limits of the plotted colorbar

    Sets lower limit of the colorbar to min and upper limit to max, also
    updates ticks on the colorbar

    Parameters
    ----------
    cbar : plt.colorbar
    min : float
    max : float 
    """

    upper = np.ceil(max + (max - min)*0.1)
    lower = np.floor(min - (max - min)*0.1)

    colorbar.mappable.set_clim(vmin=lower,vmax=upper)
    cbar_ticks = np.linspace(lower, upper, num=10, endpoint=True,)
    colorbar.set_ticks(cbar_ticks)


def on_connect(client, userdata, flags, reason_code, properties):
    """
    Subsciribe to desired topic(s)

    Subscribing in on_connect() means that if we lose the connection and
    reconnect then subscriptions will be renewed.
    """

    print("Connected with result code "+str(reason_code))
    client.subscribe(MQTT_PATH)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global im, single_pixels, area, received

    # an image is recieved from the sensor: plot the image and, if video
    # button is clicked, add frame to video
    if msg.topic == "/singlecameras/camera1/image":
        flo_arr = [struct.unpack('f', msg.payload[i:i+4])[0] for i in range(0, len(msg.payload), 4)]
        # data must be transposed to match what is shown on AtomS3 display
        thermal_img = np.array(flo_arr).reshape(24,32).T
        im.set_data(thermal_img)

        if received%10 == 0:
            # get min and max of the measured temperatures
            min = np.min(thermal_img)
            max = np.max(thermal_img)

            update_cbar(cbar, min, max)
        received += 1

        fig_text.set_text(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
        fig.canvas.draw() # draw canvas

        video.add_frame(fig)

    if msg.topic == "/singlecameras/camera1/pixels/data":
        test = list(map(str, msg.payload.decode().split(',')))
        print("Recieved: ", msg.payload.decode())
        print("Lenght: ", len(test))

    if msg.topic == "/singlecameras/camera1/pixels/current":
        # get pixels the camera is already looking at
        single_pixels.handle_mqtt(msg.payload.decode(), draw_pixel)
        single_pixels.draw_on(draw_pixel)

    if msg.topic == "/singlecameras/camera1/area/data":
        print("Area data: ", msg.payload.decode())
   
    if msg.topic == "/singlecameras/camera1/area/current":
        # get area the camera is already looking at
        area.handle_mqtt(msg.payload.decode(),ax)
        area.draw_on(ax)


def on_click(event):
    """
    Defines what to do when  there is a mouse click on the figure:
    if area button is not clicked, get point and publish it
    if it is clicked define area (only one area at the time)
    """

    global area, clicks, single_pixels

    if not event.inaxes == ax:
        # when the click is outside of the axes do nothing
        return

    # get coordinates of the mouse click
    x = np.floor(event.xdata).astype(int)
    y = np.floor(event.ydata).astype(int)

    if area_button.get_status()[0]:
        # if area button is clicked define area (two clicks are needed)
        clicks = np.append(clicks, [(x, y)], axis=0)

        if clicks.shape[0]>2:   # reset area with more than two clicks
            print("Resetting interesting area, click again")
            clicks = np.empty((0, 2), dtype=int)
            area.cleanup(ax)

        draw_clicks.set_data(clicks[:,0],clicks[:,1])

        if clicks.shape[0] == 2:
            area.cleanup(ax) # remove drawing of previous area and delete previous one
            # publish the selected area
            x_left = int(np.min(clicks, axis=0)[0])
            y_low = int(np.min(clicks, axis=0)[1])
            w = int(abs(clicks[0][0] - clicks[1][0]))
            h = int(abs(clicks[0][1] - clicks[1][1]))
            
            client.publish("/singlecameras/camera1/area", f"{x_left} {y_low} {w} {h}")
            print(f"The selected area is x,y = ({x_left} {y_low}), w = {w}, h = {h}")

            area.get_from_click(clicks)
            area.draw_on(ax) # draw current area

    else:
        # if area button is not clicked get point coordinates and publish them
        # if coordinates are already present, do not append them nor publish
        if single_pixels.get_from_click(x, y):
            client.publish("/singlecameras/camera1/pixels/coord", f"{x} {y}")   # publish pixel position
            single_pixels.draw_on(draw_pixel)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_SERVER, 1883, 60)

client.loop_start()
cid = fig.canvas.mpl_connect('button_press_event', on_click)
cursor = Cursor(ax, useblit=True, color='black', linewidth=1 )

area_button = CheckButtons(plt.axes([0.45, 0.9, 0.3, 0.075]), ['Select area',],
                           [False,], check_props={'color':'red', 'linewidth':1})
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

plt.show()

"""
    Receive data from a thermal camera MLX90640 connected to AtomS3 and display it
"""

import struct
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from matplotlib.widgets import CheckButtons
from matplotlib import patches
import cv2
import paho.mqtt.client as mqtt

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

# arrays for the coordinates of the interesting pixels and the area
single_pixels = np.empty((0, 2), dtype=int)
area = np.empty((0, 4))

clicks = np.empty((0, 2), dtype=int)

draw_pixel, = ax.plot([], [], marker='+', color='red', markersize=12, linestyle='None')
draw_area, = ax.plot([], [], marker='+', color='blue', markersize=12, linestyle='None')

received = 0    # counter for how many thermal images have been received

class Camera:
    """
    Class used to save a video of the plot
    """

    def __init__(self, size=(720,960), fps=4):
        self.filming = False
        self.size = size
        self.fps = fps

    def start_video(self):
        """
        Create a VideoWriter object

        Parameters
        ----------
        none
        """

        now = datetime.now() # current date and time
        time = now.strftime("%H_%M_%S")
        filename = "out_video/"+time+".mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video = cv2.VideoWriter(filename, fourcc, self.fps, self.size, isColor=True)
        self.filming = True
        print(f"Filming {filename}")

    def add_frame(self, fig):
        """
        Add frame to video if filming, else do nothing

        Parameters
        ----------
        fig : figure
        """

        if self.filming:
            data_arr = np.asarray(fig.canvas.renderer.buffer_rgba())
            data_arr = cv2.cvtColor(data_arr, cv2.COLOR_RGBA2BGR) # Convert to BGR (opencv's default)
            data_arr = cv2.resize(data_arr, self.size) # resize image to video size
            self.video.write(data_arr) # add image to video writer
        else:
            pass

    def stop_video(self):
        """
        Save output video

        Parameters
        ----------
        none
        """

        self.video.release()
        self.filming = False
        print(f"Stopped filming, saved output video")


videocamera = Camera()


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
    global im, single_pixels, area, filming, received

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

        videocamera.add_frame(fig)

        if (not film_video.get_status()[0]) and videocamera.filming:
            videocamera.stop_video()    # TODO: this should be moved elsewhere, to make sure 
                                        # video is saved even if the AtomS3 loses the connection

    if msg.topic == "/singlecameras/camera1/pixels/data":
        test = list(map(str, msg.payload.decode().split(',')))
        print("Recieved: ", msg.payload.decode())
        print("Lenght: ", len(test))

    if msg.topic == "/singlecameras/camera1/pixels/current":
        # get pixels the camera is already looking at
        if msg.payload.decode() == "none":
            draw_pixel.set_data(np.empty((0)),np.empty((0)))
            single_pixels = np.empty((0, 2), dtype=int)
        else:
            current = list(map(str, msg.payload.decode().split(',')))
            # add each pixel to single_pixels
            for i, pixel in enumerate(current):
                coord = list(map(int, pixel.split(' ')))
                # there is no need to check if coord. are already present, if they
                # were they would not have been published
                single_pixels = np.append(single_pixels, [coord], axis=0)
            # draw selected pixels on image
            draw_pixel.set_data(single_pixels[:,0],single_pixels[:,1])

    if msg.topic == "/singlecameras/camera1/area/data":
        print("Area data: ", msg.payload.decode())
   
    if msg.topic == "/singlecameras/camera1/area/current":
        # get area the camera is already looking at
        if msg.payload.decode() == "none":
            for p in reversed(ax.patches): # remove drawing of previous area
                p.remove()
            area = np.empty((0, 4), dtype=int)
        else:
            area = np.empty((0, 4), dtype=int)  # forget previous area information
            for p in reversed(ax.patches): # remove drawing of previous area
                p.remove()

            area = np.append(area, [list(map(int, msg.payload.decode().split(' ')))], axis=0)

            xy = (area[0][0],area[0][1])
            # get width and height
            w = area[0][2]
            h = area[0][3]
            # draw current area
            rect = patches.Rectangle(xy, w, h, linewidth=1, edgecolor='b', facecolor='none')
            ax.add_patch(rect)


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

    if select_area.get_status()[0]:
        # if area button is clicked define area (two clicks are needed)
        clicks = np.append(clicks, [(x, y)], axis=0)

        if clicks.shape[0]>2:   # reset area with more than two clicks
            print("Resetting interesting area, click again")
            area = np.empty((0, 4), dtype=int)
            clicks = np.empty((0, 2), dtype=int)
            for p in reversed(ax.patches): # remove drawing of previous area
                p.remove()
            return
        draw_area.set_data(clicks[:,0],clicks[:,1])

        if clicks.shape[0] == 2:
            # publish the selected area
            x_left = int(np.min(clicks, axis=0)[0])
            y_low = int(np.min(clicks, axis=0)[1])
            w = int(abs(clicks[0][0] - clicks[1][0]))
            h = int(abs(clicks[0][1] - clicks[1][1]))
            area = np.append(area, [(x_left, y_low, w, h)], axis=0)
            client.publish("/singlecameras/camera1/area", f"{x_left} {y_low} {w} {h}")
            print(f"The selected area is x,y = ({x_left} {y_low}), w = {w}, h = {h}")

            for p in reversed(ax.patches): # remove drawing of previous area
                p.remove()

            # draw current area
            rect = patches.Rectangle((x_left, y_low), w, h, linewidth=1, edgecolor='b', facecolor='none')
            ax.add_patch(rect)

    else:
        # if area button is not clicked get point coordinates and publish them
        # if coordinates are already present, do not append them
        if [(x, y)] not in single_pixels:
            single_pixels = np.append(single_pixels, [(x, y)], axis=0)  # append pixel to array

            # IMPORTANT: x and y in the sketch they are swapped 
            client.publish("/singlecameras/camera1/pixels/coord", f"{x} {y}")   # publish pixel position
            draw_pixel.set_data(single_pixels[:,0],single_pixels[:,1]) # draw selected pixels on image

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_SERVER, 1883, 60)

client.loop_start()
cid = fig.canvas.mpl_connect('button_press_event', on_click)
cursor = Cursor(ax, useblit=True, color='black', linewidth=1 )

select_area = CheckButtons(plt.axes([0.45, 0.9, 0.3, 0.075]), ['Select area',],
                           [False,], check_props={'color':'red', 'linewidth':1})
film_video = CheckButtons(plt.axes([0.1, 0.9, 0.3, 0.075]), ['Video',], [False,],
                          check_props={'color':'green', 'linewidth':1})

def button_callback(label):
    global videocamera
    if not videocamera.filming:
        videocamera.start_video()

film_video.on_clicked(button_callback)

plt.show()

"""
    Receive data from a thermal camera MLX90640 connected to AtomS3 and display it
"""

import struct
import sys
from datetime import datetime, timedelta
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
import paho.mqtt.client as mqtt
from loguru import logger

from THERMALCAMERA_S3.videomaker import VideoMaker
from THERMALCAMERA_S3.stuff import InterestingArea
from THERMALCAMERA_S3.stuff import InterestingPixels
from THERMALCAMERA_S3.controlpanel import ControlPanel
from THERMALCAMERA_S3.controlpanel import CameraSettings


MQTT_SERVER = "test.mosquitto.org"
MQTT_PATH = "/singlecameras/camera1/#"

def level_filter(levels):
    def is_level(record):
        return record["level"].name in levels
    return is_level

logger.remove(0)
logger.add(sys.stderr, filter=level_filter(["WARNING", "DEBUG"]))

start_time = datetime.now()
max_dead_time = timedelta(seconds=4) # in seconds
last_received = datetime.now()-timedelta(seconds=10)

fig = plt.figure(figsize=(10, 5))
gs = fig.add_gridspec(1, 2, width_ratios=[0.4, 0.6], wspace=0.15)
# create subfigures
img_fig = fig.add_subfigure(gs[0])
data_fig = fig.add_subfigure(gs[1])
# get axes
ax_img = img_fig.subplots()
# create subplots for pixels data and adjust spacing
ax_pixels, ax_area = data_fig.subplots(2, 1)
# clear space for legend and make it look right
data_fig.subplots_adjust(right=0.77, hspace=0.5, top=0.95, bottom=0.1)
img_fig.subplots_adjust(top=0.95, bottom=0.1, right=0.9, left=0.15)

# setup for image visualization
# Initialize a list of float as per the image data
im = ax_img.imshow(np.random.rand(32,24)*30+10, cmap='inferno')
time_text = img_fig.figure.text(0.4*0.05, 0.05, "Waiting for data...")
# create colorbar
cbar = plt.colorbar(im, shrink=0.8)
cbar_ticks = np.linspace(10., 40., num=7, endpoint=True)
cbar.set_ticks(cbar_ticks)
cbar.minorticks_on()

# setup for visualization of pixel data
ax_pixels.set_xlabel("Time from start [s]")
ax_pixels.set_ylabel("T [°C]")
ax_pixels.grid()
ax_pixels.margins(0.15)
pix_text = data_fig.figure.text(0.45, 0.97, "Waiting for data...")

# setup for visualization of area data
ax_area.set_xlabel("Time from start [s]")
ax_area.set_ylabel("T [°C]")
ax_area.grid()
ax_area.margins(0.15)
fig_text = fig.figure.text(0.45, 0.48, "Waiting for data...")

pixels_data = {} # will contain the pixel as a key and as a value another dict
                 #  with the times, values and Line2D

area_data = {} # will contain the area as a key and as a value another dict
               #  with the times, values and Line2D (even though only one area at the time is defined)

draw_pixel, = ax_img.plot([], [], marker='+', color='red', markersize=12, linestyle='None')
draw_clicks, = ax_img.plot([], [], marker='+', color='blue', markersize=12, linestyle='None')


clicks = np.empty((0, 2), dtype=int)    # array for mouse clicks to define area
received = 0    # counter for how many thermal images have been received

video = VideoMaker("display")

area = InterestingArea()
single_pixels = InterestingPixels()

def update_cbar(colorbar, min_temp, max_temp):
    """
    Update limits of the plotted colorbar

    Sets lower limit of the colorbar to min and upper limit to max, also
    updates ticks on the colorbar

    Parameters
    ----------
    cbar : plt.colorbar
    min_temp : float
    max_temp : float 
    """

    upper = np.ceil(max_temp + (max_temp - min_temp)*0.1)
    lower = np.floor(min_temp - (max_temp - min_temp)*0.1)

    colorbar.mappable.set_clim(vmin=lower,vmax=upper)
    ticks = np.linspace(lower, upper, num=10, endpoint=True,)
    colorbar.set_ticks(ticks)

def video_button_cb(label):

    global video
    if not video.filming:
        # when checkbox is clicked and previously the video was not being saved,
        # start video
        video.start_video()
    else:
        # if video was being taken, stop and save the file
        video.stop_video()

def on_connect(client, userdata, flags, reason_code, properties):
    """
    Subsciribe to desired topic(s)

    Subscribing in on_connect() means that if we lose the connection and
    reconnect then subscriptions will be renewed.
    """

    logger.info(f"Connected with result code {reason_code}")
    client.subscribe(MQTT_PATH)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    """
    Define what happens when a MQTT message is received
    """

    global im, single_pixels, area, received, last_received, panel

    


    if msg.topic == "/singlecameras/camera1/settings/current":
        logger.info("Received camera settings")
        # get the current camera settings
        # they are received as rate: 8.00 shift: 8.00 emissivity: 0.95 mode: 1
        logger.debug(msg.payload)
        try:
            st_settings = msg.payload.decode()
            pattern_set = r'(\w+):\s(\d+(?:\.\d+)?)'
            matches_set = re.findall(pattern_set, st_settings)

            # Convert to dictionary
            # current_set = {k: float(v) if "." in v else int(v) for k, v in matches_set}
            current_set = {k: float(v) for k, v in matches_set}

            panel.rate.set_text(current_set["rate"])
            panel.shift.set_text(current_set["shift"])
            panel.emissivity.set_text(current_set["emissivity"])
            panel.fig.canvas.draw()

        except (ValueError, KeyError):
            logger.warning(f"Received settings have invalid format: {msg.payload}")


    # an image is recieved from the sensor: plot the image and, if video
    # button is clicked, add frame to video
    if msg.topic == "/singlecameras/camera1/image":
        last_received = datetime.now()
        try:
            flo_arr = [struct.unpack('f', msg.payload[i:i+4])[0] for i in range(0, len(msg.payload), 4)]
            # data must be transposed to match what is shown on AtomS3 display
            thermal_img = np.array(flo_arr).reshape(24,32).T
            im.set_data(thermal_img)

            if received%10 == 0:
                # update colorbar according to min and max of the measured temperatures
                update_cbar(cbar, np.min(thermal_img), np.max(thermal_img))
            received += 1

            time_text.set_text(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
            fig.canvas.draw() # draw canvas

            video.add_frame(img_fig)
        except (struct.error, ValueError):
            logger.warning("Received invalid image")
            logger.debug(f"Invalid img: {msg.payload}")

    if msg.topic == "/singlecameras/camera1/pixels/data":
        try:
            # logger.debug(f"Pixel data: {msg.payload.decode()}")
            # get current pixels and data from message
            current = [list(map(float, p.split(' '))) for p in msg.payload.decode().split(",")]
            t = (datetime.now() - start_time).total_seconds()

            # now update value in dictionary or add new one if not present
            for x, y, val in current:
                if val>50:
                    logger.info(f"Pixel temperature: {val}, message is {msg.payload}")
                pixel = (int(x), int(y))
                if pixel not in pixels_data: # add to dict and make new line
                    logger.info(f"Receiving new pixel: {pixel}")
                    # create line for its data
                    l, = ax_pixels.plot([], [], label=str(pixel), color=np.random.rand(3,))
                    ax_pixels.legend(loc="upper left", bbox_to_anchor=(1,1))
                    # add (empty) data and Line2D to dict
                    pixels_data[pixel] = {"times": [], "temps": [], "line": l}
                # add values (temperature and time)
                single = pixels_data[pixel]
                single["times"].append(t)
                single["temps"].append(val)
                single["line"].set_data(single["times"], single["temps"])

            # update plot axes
            ax_pixels.relim()
            ax_pixels.autoscale_view()
            pix_text.set_text(f"Number of current pixels: {len(current)}")
        except ValueError:
            logger.warning(f"Received data has invalid format: {msg.payload}")

    if msg.topic == "/singlecameras/camera1/pixels/current":
        # get pixels the camera is already looking at
        single_pixels.handle_mqtt(msg.payload.decode(), draw_pixel)
        single_pixels.draw_on(draw_pixel)

    if msg.topic == "/singlecameras/camera1/area/data":
        try:
            # logger.debug(f"Area data: {msg.payload.decode()}")
            st = msg.payload.decode()
            pattern = r'(\w+):\s(-?\d+\.?\d?)'
            matches = re.findall(pattern, st)
            # Convert to dictionary, converting numbers to float or int automatically
            data = {k: float(v) if "." in v else int(v) for k, v in matches}

            x, y, w, h = data["x"], data["y"], data["w"], data["h"]
            fig_text.set_text(f"Area: ({int(x)}, {int(y)}), w={int(w)} h={int(h)}")

            if (data["max"] and data["min"] and data["avg"]): # values should be appended only if they are all present
                x = (datetime.now() - start_time).total_seconds()
                if str(area.a) not in area_data:
                    # create 2DLine for min, max and avg
                    l_avg, = ax_area.plot([], [], color='green', markersize=12, label=r"$T_{avg}$")
                    l_min, = ax_area.plot([], [], color='blue', markersize=12, label=r"$T_{min}$")
                    l_max, = ax_area.plot([], [], color='red', markersize=12, label=r"$T_{max}$")
                    if not hasattr(ax_area, "_legend"):
                        ax_area.legend(loc="upper left", bbox_to_anchor=(1,0.5))
                    area_data[str(area.a)] = {"times" : [], "avg" : [], "min" : [], "max" : [],
                                            "l_avg" : l_avg, "l_min" : l_min, "l_max" : l_max}
                # only the currently defined area data is getting updated
                a = area_data[str(area.a)]
                a["times"].append(x)
                a["avg"].append(data["avg"])
                a["min"].append(data["min"])
                a["max"].append(data["max"])
                a["l_avg"].set_data(a["times"], a["avg"])
                a["l_min"].set_data(a["times"], a["min"])
                a["l_max"].set_data(a["times"], a["max"])

                # update plot axes
                ax_area.relim()
                ax_area.autoscale_view()

        except (TypeError, KeyError):
            logger.warning(f"Received data has invalid format: {msg.payload}")

    if msg.topic == "/singlecameras/camera1/area/current":
        # get area the camera is already looking at
        area.handle_mqtt(msg.payload.decode(),ax_img)
        area.draw_on(ax_img)


def on_click(event):
    """
    Defines what to do when  there is a mouse click on the figure:
    if area button is not clicked, get point and publish it
    if it is clicked define area (only one area at the time)
    """

    global area, clicks, single_pixels

    if not event.inaxes == ax_img:
        # when the click is outside of the axes do nothing
        return

    # get coordinates of the mouse click
    x = np.round(event.xdata).astype(int)
    y = np.round(event.ydata).astype(int)

    if area_button.get_status()[0]:
        # if area button is clicked define area (two clicks are needed)
        clicks = np.append(clicks, [(x, y)], axis=0)

        if clicks.shape[0]>2:   # reset area with more than two clicks
            print("Click again to redefine area")
            clicks = np.empty((0, 2), dtype=int)

        draw_clicks.set_data(clicks[:,0],clicks[:,1])

        if clicks.shape[0] == 2:
            area.get_from_click(clicks)    # get defined area
            area.cleanup(ax_img) # remove drawing of previous area
            area.draw_on(ax_img) # and draw current one

            # publish the selected area
            client.publish("/singlecameras/camera1/area", str(area))
            print("The selected area is ",str(area))
            draw_clicks.set_data([],[]) # remove cliks from image

    else:
        # if area button is not clicked get point coordinates and publish them
        # if coordinates are already present, it does not append nor publish them
        if single_pixels.get_from_click(x, y):
            # publish position of the last pixel
            client.publish("/singlecameras/camera1/pixels/coord", single_pixels.new_pixel())
            single_pixels.draw_on(draw_pixel)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_SERVER, 1883, 60)


cid = fig.canvas.mpl_connect('button_press_event', on_click)

area_button = CheckButtons(plt.axes([0.4*0.45, 0.9, 0.4*0.3, 0.075]), ['Select area',],
                           [False,], check_props={'color':'red', 'linewidth':1})
video_button = CheckButtons(plt.axes([0.4*0.1, 0.9, 0.4*0.3, 0.075]), ['Video',], [False,],
                          check_props={'color':'green', 'linewidth':1})

video_button.on_clicked(video_button_cb)

def reset_px_cb(event):
    client.publish("/singlecameras/camera1/pixels/reset", "1")

def reset_a_cb(event):
    client.publish("/singlecameras/camera1/area/reset", "1")

panel = ControlPanel()
settings = CameraSettings()
panel.reset_pixels.on_clicked(reset_px_cb)
panel.reset_area.on_clicked(reset_a_cb)

def info_cb(event):
    client.publish("/singlecameras/camera1/info_request", "1")
    logger.info("Sending request to AtomS3")

panel.get_info.on_clicked(info_cb)


# TODO: it would be very nice if the box turned red when invalid values are inserted
def set_shift(expression):
    # TODO: I have no idea of the allowed range for this parameter
    try:
        settings.set_shift(int(expression))
    except ValueError:
        print("Invalid input for shift: it must be a number.")

def set_em(expression):
    try:
        em = float(expression)
        if 0. < em <= 1.:
            panel.emissivity_box.text_disp.set_color('black')
            settings.set_em(em)
        else:
            panel.emissivity_box.text_disp.set_color('red')
            print(f"Invalid emissivity: it must be between 0 and 1.")
    except ValueError:
        print("Invalid input for emissivity: it must be a number between 0 and 1.")

panel.shift_box.on_submit(set_shift)
panel.emissivity_box.on_submit(set_em)

def apply_set(event):
    logger.info("Sending new settings to AtomS3")
    client.publish("/singlecameras/camera1/settings", settings.publish_form())


def update_status():
    if datetime.now()-last_received<max_dead_time:
        panel.state.set_text("ONLINE")
        panel.state.set_color("green")
        bbox = panel.state.get_bbox_patch()
        bbox.set_facecolor((0.8, 1.0, 0.8))  # light green
        bbox.set_edgecolor((0.5, 1.0, 0.5))  # green border
    else:
        panel.state.set_text("OFFLINE")
        panel.state.set_color("red")
        bbox = panel.state.get_bbox_patch()
        bbox.set_facecolor((1.0, 0.8, 0.8))  # light red
        bbox.set_edgecolor((1.0, 0.5, 0.5))  # red border

    panel.fig.canvas.draw()

timer = panel.fig.canvas.new_timer(interval=500)
timer.add_callback(update_status)
timer.start()

def reset_set(event):
    logger.info("Sending default settings to AtomS3")
    settings.default()
    client.publish("/singlecameras/camera1/settings", settings.publish_form())

panel.apply_settings.on_clicked(apply_set)
panel.reset_settings.on_clicked(reset_set)

def mode_changed(label):
    settings.set_readout(label)

def set_rate(label):
    settings.set_rate(float(label))

panel.mode_selector.on_clicked(mode_changed)
panel.rate_selector.on_clicked(set_rate)

try:
    client.loop_start()
    plt.show()
except KeyboardInterrupt:
    plt.close("all")
    logger.info("Shutting down...")
finally:
    client.loop_stop()
    client.disconnect()

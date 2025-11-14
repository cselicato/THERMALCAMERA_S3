"""
Script to receive and plot the thermocamera data sent by the AtomS3 
"""

import struct
import sys
import time
from datetime import datetime, timedelta
import re
import numpy as np
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
from loguru import logger

from thermocam import THERMOCAM_DATA
from thermocam.videomaker import VideoMaker
from thermocam.roi import InterestingArea, InterestingPixels
from thermocam.controls import ControlPanel, CameraSettings
from thermocam.visualization import Display


MQTT_SERVER = "test.mosquitto.org"
MQTT_PATH = "/singlecameras/camera1/#"

def level_filter(levels):
    """
    Filter function for Loguru that allows only specified levels.

    Parameters
    ----------
    levels : list[str]
        Log level names to include

    Returns
    -------
    callable
        Function usable as Loguru's `filter` argument.
    """
    def is_level(record):
        return record["level"].name in levels
    return is_level

logger.remove(0)
logger.add(sys.stderr, filter=level_filter(["WARNING", "ERROR"]))

SAVE_FILE = True
if SAVE_FILE:
    curr_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    f_pix = open(THERMOCAM_DATA / f"pix_{curr_time}.txt",'w', encoding="utf-8")
    f_area = open(THERMOCAM_DATA / f"area_{curr_time}.txt",'w', encoding="utf-8")

start_time = datetime.now()
max_dead_time = timedelta(seconds=4) # in seconds
last_received = datetime.now()-timedelta(seconds=10)


clicks = np.empty((0, 2), dtype=int)    # array for mouse clicks to define area
received = 0    # counter for how many thermal images have been received

figure = Display()
panel = ControlPanel()

video = VideoMaker()
settings = CameraSettings()
area = InterestingArea()
single_pixels = InterestingPixels()


# MQTT CALLBACKS
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

    # if the received message is empty, ignore it
    if not msg.payload:
        logger.warning(f"Received empty message on topic {msg.topic}")

    global single_pixels, area, figure, received, last_received, panel

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
            flo_arr = [struct.unpack('f', msg.payload[i:i+4])[0]
                       for i in range(0, len(msg.payload), 4)]
            # data must be transposed to match what is shown on AtomS3 display
            thermal_img = np.array(flo_arr).reshape(24,32).T
            figure.image.set_data(thermal_img)

            if received%10 == 0:
                # update colorbar according to min and max of the measured temperatures
                figure.update_cbar(np.min(thermal_img), np.max(thermal_img))

            received += 1

            figure.time_text.set_text(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
            figure.canvas.draw() # draw canvas

            video.add_frame(figure, figure.img_dimensions())
        except (struct.error, ValueError):
            logger.warning("Received invalid image")
            logger.debug(f"Invalid img: {msg.payload}")

    if msg.topic == "/singlecameras/camera1/pixels/current":
        # get pixels the camera is already looking at
        single_pixels.handle_mqtt(msg.payload.decode(), figure.draw_pixel)
        single_pixels.draw_on(figure.draw_pixel)

    if msg.topic == "/singlecameras/camera1/pixels/data":
        single_pixels.update_data(msg.payload.decode(), figure.ax_pixels, start_time)
        figure.pix_text.set_text(f"Number of current pixels: {len(single_pixels.p)}")

        if SAVE_FILE:
            f_pix.write(f"{datetime.now()},{single_pixels.out_data()}\n")

    if msg.topic == "/singlecameras/camera1/area/current":
        # get area the camera is already looking at
        area.handle_mqtt(msg.payload.decode(),figure.ax_img)
        area.draw_on(figure.ax_img)

    if msg.topic == "/singlecameras/camera1/area/data":
        area.update_data(msg.payload.decode(), figure.ax_area, start_time)
        # NOTE: if current area (persistent message) is not received it does not work
        if area.defined(): # TODO: ugly
            x, y, w, h = area.a[0][:]
            figure.area_text.set_text(f"Area: ({x},{y}), w={w}, h={h}")
            if SAVE_FILE:
                f_area.write(f"{datetime.now()}, {area.out_data()}\n")
        else:
            logger.info("No current area...")




# CALLBACK FOR MOUSE CLICK
def on_click(event):
    """
    Defines what to do when  there is a mouse click on the figure:
    if area button is not clicked, get point and publish it
    if it is clicked define area (only one area at the time)
    """

    global area, clicks, single_pixels

    if not event.inaxes == figure.ax_img:
        # when the click is outside of the axes do nothing
        return

    # get coordinates of the mouse click
    x = np.round(event.xdata).astype(int)
    y = np.round(event.ydata).astype(int)

    if figure.area_button.get_status()[0]:
        # if area button is clicked define area (two clicks are needed)
        clicks = np.append(clicks, [(x, y)], axis=0)

        if clicks.shape[0]>2:   # reset area with more than two clicks
            logger.info("Click again to redefine area")
            clicks = np.empty((0, 2), dtype=int)

        figure.draw_clicks.set_data(clicks[:,0],clicks[:,1])

        if clicks.shape[0] == 2:
            area.get_from_click(clicks)    # get defined area
            area.cleanup(figure.ax_img) # remove drawing of previous area
            area.draw_on(figure.ax_img) # and draw current one

            # publish the selected area
            client.publish("/singlecameras/camera1/area", area.pub_area())
            figure.draw_clicks.set_data([],[]) # remove cliks from image

    else:
        # if area button is not clicked get point coordinates and publish them
        # if coordinates are already present, it does not append nor publish them
        if single_pixels.get_from_click(x, y):
            # publish position of the last pixel
            client.publish("/singlecameras/camera1/pixels/coord", single_pixels.new_pixel())
            single_pixels.draw_on(figure.draw_pixel)
# connect mouse click to callback
cid = figure.canvas.mpl_connect('button_press_event', on_click)


def video_button_cb(label):
    """ Callback for video checkbox: when checked it starts the video,
        and it stops it when i is no longer on    

    Parameters
    ----------
        label
    """
    global video
    if not video.filming:
        # when checkbox is clicked and previously the video was not being saved,
        # start video
        video.start_video()
    else:
        # if video was being taken, stop and save the file
        video.stop_video()

figure.video_button.on_clicked(video_button_cb)

# callbacks for control panel buttons
def reset_px_cb(event):
    """Publish pixel reset message
    """
    client.publish("/singlecameras/camera1/pixels/reset", "1")

def reset_a_cb(event):
    """Publish pixel reset message
    """
    client.publish("/singlecameras/camera1/area/reset", "1")

def info_cb(event):
    """Publish message for information request
    """
    client.publish("/singlecameras/camera1/info_request", "1")
    logger.info("Sending request to AtomS3")

def apply_set(event):
    """Publish selected settings
    """
    logger.info("Sending new settings to AtomS3")
    client.publish("/singlecameras/camera1/settings", settings.publish_form())

def reset_set(event):
    """Publish default settings
    """
    logger.info("Sending default settings to AtomS3")
    settings.default()
    client.publish("/singlecameras/camera1/settings", settings.publish_form())

panel.reset_pixels.on_clicked(reset_px_cb)
panel.reset_area.on_clicked(reset_a_cb)
panel.get_info.on_clicked(info_cb)
panel.apply_settings.on_clicked(apply_set)
panel.reset_settings.on_clicked(reset_set)

# callbacks for textboxes on control panel
# TODO: it would be very nice if the box turned red when invalid values are inserted
def set_shift(expression):
    """Set shift value
    """
    # TODO: I have no idea of the allowed range for this parameter
    try:
        settings.set_shift(expression)
    except ValueError:
        logger.warning("Invalid input for shift: it must be a number.")

def set_em(expression):
    """Set shift value
    """
    try:
        em = float(expression)
        if 0. < em <= 1.:
            panel.emissivity_box.text_disp.set_color('black')
            settings.set_em(em)
        else:
            panel.emissivity_box.text_disp.set_color('red') # TODO: broken (or maybe not)
            logger.warning("Invalid emissivity: it must be between 0 and 1.")
    except ValueError:
        logger.warning("Invalid input for emissivity: it must be a number between 0 and 1.")

panel.shift_box.on_submit(set_shift)
panel.emissivity_box.on_submit(set_em)

# callbacks for menus on control panel
def mode_changed(label):
    """Set readout mode
    """
    settings.set_readout(label)

def set_rate(label):
    """Set rate value
    """
    settings.set_rate(float(label))

panel.mode_selector.on_clicked(mode_changed)
panel.rate_selector.on_clicked(set_rate)

def update_status():
    """
    If last image from AtomS3 has been received less than 5 s ago,
    display status as online, else as offline
    """
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

if __name__ == "__main__":
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(MQTT_SERVER, 1883, 60)

        client.publish("/singlecameras/camera1/info_request", "1")
        time.sleep(0.5)
        client.loop_start()
        plt.show()
    except OSError as e:
        if e.errno == 101:
            logger.error("Network is unreachable, check internet connection or try later :(")
        else:
            logger.error(f"Connection failed: {e}")
    except KeyboardInterrupt:
        plt.close("all")
        logger.info("Shutting down...")
    finally:
        if SAVE_FILE:
            f_pix.close()
            f_area.close()
        client.loop_stop()
        client.disconnect()

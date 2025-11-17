"""
Callbacks module for GUI interaction and MQTT message handling
"""

import numpy as np
from loguru import logger

from thermocam import MQTT_PATH


class GUICallbacks():
    """ Defines all callback functions used by the GUI in the Display and ControlPanel

    Contains event handlers for mouse clicks on the thermal image,
    control panel buttons, checkbox toggles, text box input, and menu
    selections. Each callback delegates the execution of the action to the
    handler (instance of the class ThermoHandler)

    Parameters
    ----------
    handler : thermocam.handler.ThermoHandler
    """
    def __init__(self, handler):
        self.h = handler

    def on_click(self, event):
        """
        Handle mouse clicks on the thermal image display.

        Depending on the state of the "Select area" checkbox, it can select single
        pixels (checkbutton OFF) or an area (ON).

        A click records a single pixel. If the pixel is new, its coordinates
        are published over MQTT and drawn on the figure.

        Two clicks define a rectangular area. After the second click, the
        area is computed, drawn, and published over MQTT. A third click resets
        the selection to allow defining a new area.

        Clicks outside the image axes are ignored.

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent
            The mouse event triggered by the click
        """
        if not event.inaxes == self.h.figure.ax_img:
            # when the click is outside of the axes do nothing
            return

        # get coordinates of the mouse click
        x = np.round(event.xdata).astype(int)
        y = np.round(event.ydata).astype(int)

        if self.h.figure.area_button.get_status()[0]:
            # if area button is clicked define area (two clicks are needed)
            self.h.clicks = np.append(self.h.clicks, [(x, y)], axis=0)

            if self.h.clicks.shape[0]>2:   # reset area with more than two clicks
                logger.info("Click again to redefine area")
                self.h.clicks = np.empty((0, 2), dtype=int)

            self.h.figure.draw_clicks(self.h.clicks)

            if self.h.clicks.shape[0] == 2:
                self.h.area.get_from_click(self.h.clicks)    # get defined area
                self.h.figure.update_area(self.h.area)    #update drawn area
                # publish the selected area
                self.h.client.publish("/singlecameras/camera1/area", self.h.area.pub_area())

        else:
            # if area button is not clicked get point coordinates and publish them
            # if coordinates are already present, it does not append nor publish them
            if self.h.single_pixels.get_from_click(x, y):
                # publish position of the last pixel
                self.h.client.publish("/singlecameras/camera1/pixels/coord",
                                      self.h.single_pixels.new_pixel())
                self.h.figure.update_pixels(self.h.single_pixels)

    def video_button_cb(self, label):
        """
        Callback executed when "Video" checkbox changes state:
        - if video recording is off, it starts the video
        - if the video is being recorde, it stops it and saves the file    

        Parameters
        ----------
        label : str
            Argument needed for compatibility with matplotlib widgets
        """
        if not self.h.video.filming:
            # when checkbox is clicked and previously the video was not being saved,
            # start video
            self.h.video.start_video()
        else:
            # if video was being taken, stop and save the file
            self.h.video.stop_video()


    # callbacks for control panel buttons
    def reset_px_cb(self, event):
        """
        Publish a request to reset all selected single pixels.

        Parameters
        ----------
        event : Event
            Button press event
        """
        self.h.client.publish("/singlecameras/camera1/pixels/reset", "1")

    def reset_a_cb(self, event):
        """
        Publish a request to reset the selected area.

        Parameters
        ----------
        event : Event
            Button press event
        """
        self.h.client.publish("/singlecameras/camera1/area/reset", "1")

    def info_cb(self, event):
        """
        Request an information update from the AtomS3 device.

        Sends an MQTT message asking the device to publish the current settings,
        pixels and area

        Parameters
        ----------
        event : Event
            Button press event
        """
        self.h.client.publish("/singlecameras/camera1/info_request", "1")
        logger.info("Sending request to AtomS3")

    def apply_set(self, event):
        """
        Publish the current settings to the AtomS3 device.

        Parameters
        ----------
        event : Event
            Button press event
        """
        logger.info("Sending new settings to AtomS3")
        self.h.client.publish("/singlecameras/camera1/settings", self.h.settings.publish_form())

    def reset_set(self, event):
        """
        Restore default settings and publish them to the device.

        Parameters
        ----------
        event : Event
            Button press event
        """
        logger.info("Sending default settings to AtomS3")
        self.h.settings.default()
        self.h.client.publish("/singlecameras/camera1/settings", self.h.settings.publish_form())

    # callbacks for textboxes on control panel
    def set_shift(self, expression):
        """
        Set the detector shift value based on textbox content.

        Parameters
        ----------
        expression : str
            The value typed into the textbox. Must be convertible to float
        """
        # TODO: I have no idea of the allowed range for this parameter
        try:
            self.h.settings.shift = float(expression)
        except ValueError:
            logger.warning("Invalid input for shift: it must be a number.")

    def set_em(self, expression):
        """
        Set the emissivity value based on textbox input.

        Acceptable range is 0 < emissivity <= 1.  
        Invalid input triggers a warning and highlights the textbox in red.

        Parameters
        ----------
        expression : str
            The value typed into the textbox. Must be convertible to float
        """
        try:
            em = float(expression)
            if 0. < em <= 1.:
                self.h.panel.emissivity_box.text_disp.set_color('black')
                self.h.settings.emissivity = em
            else:
                self.h.panel.emissivity_box.text_disp.set_color('red')
                logger.warning("Invalid emissivity: it must be between 0 and 1.")
        except ValueError:
            logger.warning("Invalid input for emissivity: it must be a number.")

    # callbacks for menus on control panel
    def mode_changed(self, label):
        """
        Update the selected readout mode.

        Parameters
        ----------
        label : str
            The readout mode selected from the menu
        """
        self.h.settings.mode = label


    def set_rate(self, label):
        """
        Update the acquisition rate.

        Parameters
        ----------
        label : str
            The rate value from the menu, converted to float
        """
        self.h.settings.rate = float(label)


class MQTTCallbacks():
    """Acts as an intermediary between the MQTT client and the handler

    Defines the MQTT calbacks that are executed when the client connects
    and when a message is received-
    It does not actually process the data, the processing is done by the
    handler.

    Parameters
    ----------
    handler : thermocam.handler.ThermoHandler
    """
    def __init__(self, handler):
        self.h = handler

    def on_connect(self, client, userdata, flags, reason_code, properties):
        """
        Callback executed when the MQTT client successfully connects to the broker

        Upon connection, this function subscribes to the topic(s) defined by
        `MQTT_PATH`. Subscribing inside the connection callback ensures that
        subscriptions are not lost if the client disconnects and reconnects

        Parameters
        ----------
        client : paho.mqtt.client.Client
        userdata : any
        flags : dict
        reason_code : int
        properties : paho.mqtt.properties.Properties
        """

        logger.info(f"Connected with result code {reason_code}")
        client.subscribe(MQTT_PATH)

    def on_message(self, client, userdata, msg):
        """
        Callback executed when the MQTT client receives a message
    
        Parameters
        ----------
        client : paho.mqtt.client.Client
        userdata : any
        msg : paho.mqtt.client.MQTTMessage
        """
        self.h.handle_message(msg)

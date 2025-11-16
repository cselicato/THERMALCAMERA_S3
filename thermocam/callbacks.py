import numpy as np
from loguru import logger


# TODO: could this path be moved to a config file?
MQTT_PATH = "/singlecameras/camera1/#"


class GUICallbacks():
    """ Class used to define every single callback needed for the GUI.

    The callbacks are connected to the appropriate widget by the handler, not by
    this class.
    """
    def __init__(self, handler):
        self.h = handler

    def on_click(self, event):
        """
        Defines what to do when  there is a mouse click on the figure:
        if area button is not clicked, get point and publish it
        if it is clicked define area (only one area at the time)
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
        """ Callback for video checkbox: when checked it starts the video,
            and it stops it when i is no longer on    

        Parameters
        ----------
            label
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
        """Publish pixel reset message
        """
        self.h.client.publish("/singlecameras/camera1/pixels/reset", "1")

    def reset_a_cb(self, event):
        """Publish pixel reset message
        """
        self.h.client.publish("/singlecameras/camera1/area/reset", "1")

    def info_cb(self, event):
        """Publish message for information request
        """
        self.h.client.publish("/singlecameras/camera1/info_request", "1")
        logger.info("Sending request to AtomS3")

    def apply_set(self, event):
        """Publish selected settings
        """
        logger.info("Sending new settings to AtomS3")
        self.h.client.publish("/singlecameras/camera1/settings", self.h.settings.publish_form())

    def reset_set(self, event):
        """Publish default settings
        """
        logger.info("Sending default settings to AtomS3")
        self.h.settings.default()
        self.h.client.publish("/singlecameras/camera1/settings", self.h.settings.publish_form())

    # callbacks for textboxes on control panel
    def set_shift(self, expression):
        """Set shift value
        """
        # TODO: I have no idea of the allowed range for this parameter
        try:
            self.h.settings.shift = float(expression)
        except ValueError:
            logger.warning("Invalid input for shift: it must be a number.")

    def set_em(self, expression):
        """Set shift value
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
        """Set readout mode
        """
        self.h.settings.mode = label


    def set_rate(self, label):
        """Set rate value
        """
        self.h.settings.rate = float(label)


class MQTTCallbacks():
    """Fa da intermediario tra il client e l'handler
    """
    def __init__(self, handler):
        self.h = handler
    
    def on_connect(self, client, userdata, flags, reason_code, properties):
        """
        Subsciribe to desired topic(s)

        Subscribing in on_connect() means that if we lose the connection and
        reconnect then subscriptions will be renewed.
        """

        logger.info(f"Connected with result code {reason_code}")
        client.subscribe(MQTT_PATH)

    def on_message(self, client, userdata, msg):
        """
        Define what happens when a MQTT message is received
        """
        self.h.handle_message(msg)

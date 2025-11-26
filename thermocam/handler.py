"""Define the object that handles everything else: the MQTT callbaks, the GUI and the data
"""

from datetime import datetime, timedelta
import re
import numpy as np
from loguru import logger

from thermocam import THERMOCAM_DATA
from thermocam.videomaker import VideoMaker
from thermocam.roi import InterestingArea, InterestingPixels
from thermocam.settings import ControlPanel, CameraSettings
from thermocam.visualization import Display
from thermocam.callbacks import GUICallbacks


class ThermoHandler():
    """Central handler for GUI elements, MQTT message processing, and output data.

    Connects everything together

    Parameters
    ----------
    save : bool, optional
        If True, pixel and area data received from the device are written to
        timestamped text files, default is True
    max_dead_time : timedelta, optional
        Maximum allowed delay between frames before the device is considered
        offline, dafault is 2 s

    Attributes
        ----------
        client : paho.mqtt.client.Client or None
            MQTT client instance (must be assigned externally).
        start_time : datetime
            Time when the handler was created, used to timestamp incoming data.
        last_received : datetime
            Timestamp of the last received image frame.
        clicks : np.ndarray
            Stores pairs of (x, y) coordinates used to define selected area.
        figure : Display
            GUI display and plotting manager.
        panel : ControlPanel
            Interactive settings panel.
        video : VideoMaker
            Video recording manager.
        settings : CameraSettings
            Stores user-selected camera configuration.
        area : InterestingArea
            Object for handling selected rectangular ROI.
        single_pixels : InterestingPixels
            Object for handling selected individual pixels.
        f_pix, f_area : file or None
            Output files for data, if saving is enabled.
    """

    def __init__(self, save=True,max_dead_time = timedelta(seconds=2)):
        self.client = None

        self.start_time = datetime.now()
        self.max_dead_time = max_dead_time
        self.last_received = datetime.now()-timedelta(seconds=10)
        self.clicks = np.empty((0, 2), dtype=int)    # array for mouse clicks to define area
        self.figure = Display()
        self.panel = ControlPanel()
        self.video = VideoMaker()
        self.settings = CameraSettings()
        self.area = InterestingArea()
        self.single_pixels = InterestingPixels()

        cb = GUICallbacks(self)
        self.figure.canvas.mpl_connect("button_press_event", cb.on_click)
        self.figure.video_button.on_clicked(cb.video_button_cb)
        self.panel.reset_pixels.on_clicked(cb.reset_px_cb)
        self.panel.reset_area.on_clicked(cb.reset_a_cb)
        self.panel.get_info.on_clicked(cb.info_cb)
        self.panel.apply_settings.on_clicked(cb.apply_set)
        self.panel.reset_settings.on_clicked(cb.reset_set)

        self.panel.shift_box.on_submit(cb.set_shift)
        self.panel.emissivity_box.on_submit(cb.set_em)

        self.panel.mode_selector.on_clicked(cb.mode_changed)
        self.panel.rate_selector.on_clicked(cb.set_rate)

        # gets updated with new image
        self.last_received = datetime.now() - timedelta(seconds=10)

        self.canvas = self.panel.fig.canvas
        self.timer = self.figure.canvas.new_timer(interval=500)  # 500 ms
        self.timer.add_callback(self.update_status)             # callback
        self.timer.start()

        # stuff for saving files
        self.save = save
        self.f_pix = None
        self.f_area = None

        if save:
            curr_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.f_pix = open(THERMOCAM_DATA / f"pix_{curr_time}.txt", 'w', encoding="utf-8")
            self.f_area = open(THERMOCAM_DATA / f"area_{curr_time}.txt", 'w', encoding="utf-8")
     


    # MQTT CALLBACK
    def handle_message(self, msg):
        """Process incoming MQTT messages from the AtomS3

        According to the topic, it:
        - displays the thermal image
        - updates pixels and area selection by drawing the current ones
        - updates the live plots of the pixels and area data
        - records video (of the thermal image)
        - displays current settings ot the thermal camera in the contol panel

        Parameters
        ----------
        msg : paho.mqtt.client.MQTTMessage
            received MQTT message
        """
        # if the received message is empty, ignore it
        if not msg.payload:
            logger.warning(f"Received empty message on topic {msg.topic}")

        if msg.topic == "/singlecameras/camera1/settings/current":
            logger.info("Received camera settings")
            # get the current camera settings and display them on contol panel
            # they are received as rate: 8.00 shift: 8.00 emissivity: 0.95 mode: 1
            logger.debug(msg.payload)
            try:
                st_settings = msg.payload.decode()
                pattern_set = r'(\w+):\s(\d+(?:\.\d+)?)'
                matches_set = re.findall(pattern_set, st_settings)

                # Convert to dictionary
                current_set = {k: float(v) for k, v in matches_set}

                self.panel.rate.set_text(current_set["rate"])
                self.panel.shift.set_text(current_set["shift"])
                self.panel.emissivity.set_text(current_set["emissivity"])
                if current_set["mode"] == 0:
                    self.panel.mode.set_text("Chess")
                else:
                    self.panel.mode.set_text("  TV")
                self.panel.fig.canvas.draw()

            except (ValueError, KeyError):
                logger.warning(f"Received settings have invalid format: {msg.payload}")


        # an image is recieved from the sensor: plot the image and, if video
        # button is clicked, add frame to video
        if msg.topic == "/singlecameras/camera1/image":
            self.last_received = datetime.now()
            self.figure.update_image(msg)
            self.video.add_frame(self.figure, self.figure.img_dimensions())

        if msg.topic == "/singlecameras/camera1/pixels/current":
            # get pixels the camera is already looking at
            self.single_pixels.handle_mqtt(msg.payload.decode())
            self.figure.update_pixels(self.single_pixels)

        if msg.topic == "/singlecameras/camera1/pixels/data":
            self.single_pixels.update_data(msg.payload.decode(),
                                           self.figure.ax_pixels, self.start_time)
            self.figure.pix_text.set_text(f"Number of current pixels: {len(self.single_pixels.p)}")

            if self.save and self.f_pix:
                self.f_pix.write(f"{datetime.now()},{self.single_pixels.out_data()}\n")

        if msg.topic == "/singlecameras/camera1/area/current":
            # get area the camera is already looking at
            self.area.handle_mqtt(msg.payload.decode())
            self.figure.update_area(self.area)

        if msg.topic == "/singlecameras/camera1/area/data":
            self.area.update_data(msg.payload.decode(), self.figure.ax_area, self.start_time)
            # NOTE: if current area (persistent message) is not received it does not work
            if self.area.defined(): # TODO: ugly
                x, y, w, h = self.area.a[0][:]
                self.figure.area_text.set_text(f"Area: ({x},{y}), w={w}, h={h}")
                if self.save and self.f_area:
                    self.f_area.write(f"{datetime.now()}, {self.area.out_data()}\n")
            else:
                logger.info("No current area...")

    def update_status(self):
        """
        Update the device status on the control panel.

        If last image from AtomS3 has been received within max_dead_time, it
        display ONLINE status, otherwise as OFFLINE.

        This method is meant to be periodically executed by a timer
        """
        if datetime.now()-self.last_received<self.max_dead_time:
            self.panel.online()
        else:
            self.panel.offline()

    def close_files(self):
        """ Close pixel and area output files if they were opened.
        """
        if self.f_pix:
            self.f_pix.close()
        if self.f_area:
            self.f_area.close()

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.widgets import TextBox
from matplotlib.widgets import RadioButtons


class ControlPanel:
    """
    Create the control panel with all the useful settings of the camera

    Functionalities:
    - reset pixels
    - reset area
    
    """

    def __init__(self):
        self.fig = plt.figure(figsize=(5, 4))
        fig = self.fig
        fig.suptitle("THERMALCAMERA CONTROL PANEL", fontsize=16)
        # settings = fig.text(0.12, 0.85, "MLX90640 settings ")
        settings = self.fig.text(0.35, 0.85, "Current:")

        # buttons to reset pixel and area
        self.reset_pixels = Button(plt.axes([0.13+0.5, 0.75, 0.24, 0.075]), "Reset pixels")
        self.reset_area = Button(plt.axes([0.13+0.5, 0.65, 0.24, 0.075]), "Reset area")

        # buttons to set camera settings
        # w = 0.2
        w = 0.1
        x = 0.2
        self.rate_box = TextBox(fig.add_axes([x, 0.9-0.15, w, 0.075]), "Refresh rate:", textalignment="center")
        self.shift_box = TextBox(fig.add_axes([x, 0.8-0.15, w, 0.075]), "Shift:", textalignment="center")
        self.emissivity_box = TextBox(fig.add_axes([x, 0.7-0.15, w, 0.075]), "Emissivity:", textalignment="center")
        self.rate = fig.text(x+w+0.05, 0.9-0.13, "...")
        self.shift = fig.text(x+w+0.05, 0.8-0.13, "...")
        self.emissivity = fig.text(x+w+0.05, 0.7-0.13, "...")





        self.apply_settings = Button(plt.axes([0.13, 0.15+0.05, 0.24, 0.075]), "APPLY SETTINGS")
        self.reset_settings = Button(plt.axes([0.13, 0.0375+0.05, 0.24, 0.075]), "RESET SETTINGS")

        modes = fig.text(0.12, 0.5, "Readout mode:")
        radio_ax = plt.axes([0.1, 0.34, 0.3, 0.15])
        self.mode_selector = RadioButtons(radio_ax, ('Chess pattern', 'TV interleave'))#, active=0)

        t = fig.text(0.62, 0.45, "AtomS3 state:",fontsize=13)
        self.state = fig.text(0.68, 0.35, "OFFLINE",fontsize=13,color="red",
                bbox=dict(boxstyle="round",
                   ec=(1., 0.5, 0.5),
                   fc=(1., 0.8, 0.8),
                   ))

        self.get_info = Button(plt.axes([0.13+0.5, 0.0375+0.1, 0.24, 0.075]), "Request settings")



class CameraSettings:
    def __init__(self):
        # initialize with default values
        self.settings = {"rate" : 2, "shift" : 8, "emissivity" : 0.95, "mode": 0}

    def set_rate(self, r):
        self.settings["rate"] = r

    def set_shift(self, s):
        self.settings["shift"] = s
    
    def set_em(self, e):
        self.settings["emissivity"] = e

    def set_readout(self, mode):
        if mode == 'Chess pattern':
            self.settings["mode"] = 0
        elif mode == 'TV interleave':
            self.settings["mode"] = 1
        else:
            print(f"Readout mode {mode} is unknown, using default chess pattern.")
            self.settings["mode"] = 0
    
    def publish_form(self):
        # the rate must become a number between 0 and 7
        # conversion = {0.5:"0x00", 1:"0x01", 2:"0x02", 4:"0x03", 8:"0x04", 16:"0x05", 32:"0x06", 64:"0x07"}
        conversion = {0.5: 0, 1: 1, 2: 2, 4: 3, 8:4, 16:5, 32:6, 64:7}
        converted = conversion[self.settings["rate"]]

        string = f"{converted}\n{self.settings["shift"]}\n{self.settings["emissivity"]}\n{self.settings["mode"]}\n"
        return string
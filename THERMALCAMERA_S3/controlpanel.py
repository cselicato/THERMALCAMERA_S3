import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.widgets import TextBox
from matplotlib.widgets import RadioButtons
from matplotlib.patches import FancyBboxPatch
from loguru import logger


class ControlPanel:
    """
    Create the control panel with all the useful settings of the camera

    Functionalities:
    - reset pixels
    - reset area
    - set camera settings
    
    """

    def __init__(self):
        self.fig = plt.figure(figsize=(5, 4))
        fig = self.fig
        fig.suptitle("THERMAL CAMERA CONTROL PANEL", fontsize=16, fontweight='bold')
        fig.text(0.08, 0.88, "Cam settings:", fontsize=12, fontweight='bold')
        self.fig.text(0.35, 0.85, "Current:", fontweight='bold')

        # buttons to reset pixel and area
        self.reset_pixels = Button(plt.axes([0.13+0.5, 0.75, 0.24, 0.075]), "Reset pixels")
        self.reset_area = Button(plt.axes([0.13+0.5, 0.65, 0.24, 0.075]), "Reset area")

        # buttons to set camera settings
        w = 0.1
        x = 0.2
        y = 0.15
        fig.text(0.1, 0.8, "Refresh Rate [Hz]:", fontsize=10)
        rate_ax = plt.axes([0.1, 0.58, 0.16, 0.2])
        self.rate_selector = RadioButtons(rate_ax, (0.5, 1, 2, 4, 8))
        self.shift_box = TextBox(fig.add_axes([x, 0.8-0.15-y, w, 0.075]), "Shift:", textalignment="center")
        self.emissivity_box = TextBox(fig.add_axes([x, 0.7-0.15-y, w, 0.075]), "Emissivity:", textalignment="center")
        self.rate = fig.text(x+w+0.05, 0.9-0.13-y, "...")
        self.shift = fig.text(x+w+0.05, 0.8-0.13-y, "...")
        self.emissivity = fig.text(x+w+0.05, 0.7-0.13-y, "...")

        self.apply_settings = Button(plt.axes([0.13, 0.15+0.05-y, 0.24, 0.075]), "APPLY SETTINGS")
        self.reset_settings = Button(plt.axes([0.13+0.5, 0.55, 0.24, 0.075]), "RESET SETTINGS")

        fig.text(0.12, 0.5-y, "Readout mode:", fontsize=12, fontweight='bold')
        radio_ax = plt.axes([0.1, 0.34-y, 0.3, 0.15])
        self.mode_selector = RadioButtons(radio_ax, ('Chess pattern', 'TV interleave'))#, active=0)

        fig.text(0.62, 0.45,"Status:", fontsize=12, fontweight='bold')
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
    
    def default(self):
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
            logger.warning(f"Readout mode {mode} is unknown, using default chess pattern.")
            self.settings["mode"] = 0
    
    def publish_form(self):
        # the rate must become a number between 0 and 7
        conversion = {0.5: 0, 1: 1, 2: 2, 4: 3, 8:4, 16:5, 32:6, 64:7} # TODO: allowed up to 8
        converted = conversion[self.settings["rate"]]

        string = f"{converted}\n{self.settings["shift"]}\n{self.settings["emissivity"]}\n{self.settings["mode"]}\n"
        logger.debug(f"Publishing {string}")
        return string

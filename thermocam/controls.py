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
    - Reset pixels and area
    - Adjust camera refresh rate, shift, and emissivity
    - Change readout mode
    - Apply or reset settings
    - Display connection status
    
    """

    def __init__(self, figsize=(5, 4)):
        self.fig = plt.figure(figsize=figsize)
        self._setup_labels()
        self._reset_buttons()
        self._settings()
        self._status_display()

    def _setup_labels(self):
        """ Configure labels and title (should not be changed)
        """
        fig = self.fig
        fig.suptitle("THERMAL CAMERA CONTROL PANEL", fontsize=16, fontweight='bold')
        fig.text(0.08, 0.88, "Cam settings:", fontsize=12, fontweight='bold')
        fig.text(0.35, 0.85, "Current:", fontweight='bold')

    def _reset_buttons(self):
        """ Configure buttons to reset pixels and area
        """
        self.reset_pixels = Button(plt.axes([0.63, 0.75, 0.24, 0.075]), "Reset pixels")
        self.reset_area = Button(plt.axes([0.63, 0.65, 0.24, 0.075]), "Reset area")

    def _settings(self):
        """ Configure controls for camera, apply and reset button
        """
        fig = self.fig
        # menu for refresh rate
        fig.text(0.1, 0.8, "Refresh Rate [Hz]:", fontsize=10)
        self.rate_selector = RadioButtons(plt.axes([0.1, 0.58, 0.16, 0.2]), (0.5, 1, 2, 4, 8))

        # textboxes for shift and emissivity
        self.shift_box = TextBox(fig.add_axes([0.2, 0.5, 0.1, 0.075]),
                                 "Shift:", textalignment="center")
        self.emissivity_box = TextBox(fig.add_axes([0.2, 0.4, 0.1, 0.075]),
                                      "Emissivity:", textalignment="center")

        # text to display current settings
        self.rate = fig.text(0.35, 0.69, "...")
        self.shift = fig.text(0.35, 0.52, "...")
        self.emissivity = fig.text(0.35, 0.42, "...")

        # menu for readout mode
        fig.text(0.12, 0.35, "Readout mode:", fontsize=12, fontweight='bold')
        radio_ax = plt.axes([0.1, 0.19, 0.3, 0.15])
        self.mode_selector = RadioButtons(radio_ax, ('Chess pattern', 'TV interleave'))#, active=0)



        # buttons to apply/reset settings
        self.apply_settings = Button(plt.axes([0.13, 0.05, 0.24, 0.075]), "APPLY SETTINGS")
        self.reset_settings = Button(plt.axes([0.63, 0.55, 0.24, 0.075]), "RESET SETTINGS")
        # button to request current settings, pixels and area
        self.get_info = Button(plt.axes([0.63, 0.1375, 0.24, 0.075]), "Request info")

    def _status_display(self):
        """ Add current camera status (online/offline)
        """
        fig = self.fig
        fig.text(0.62, 0.45,"Status:", fontsize=12, fontweight='bold')
        self.state = fig.text(0.68, 0.35, "OFFLINE",fontsize=13,color="red",
                bbox=dict(boxstyle="round",
                   ec=(1., 0.5, 0.5),
                   fc=(1., 0.8, 0.8),
                   ))
        # TODO: methods to update status


class CameraSettings:
    """
    Define object that contains the camera setings
    """

    def __init__(self):
        # initialize with default values
        self.settings = {"rate" : 2, "shift" : 8, "emissivity" : 0.95, "mode": 0}

    def default(self):
        """
        Set default values
        """
        self.settings = {"rate" : 2, "shift" : 8, "emissivity" : 0.95, "mode": 0}

    def set_rate(self, r):
        """Set rate in Hz

        Parameters
        ----------
        r : floar
            rate
        """
        self.settings["rate"] = r

    def set_shift(self, s):
        """Set shift

        Parameters
        ----------
        s : float
            shift
        """
        self.settings["shift"] = s

    def set_em(self, e):
        """Set emissivity

        Parameters
        ----------
        e : float
            emissivity, must be between 0 and 1
        """
        self.settings["emissivity"] = e

    def set_readout(self, mode):
        """Set readout mode (chess or TV interleave)

        Parameters
        ----------
        mode 
        """
        if mode == 'Chess pattern' or mode == 0:
            self.settings["mode"] = 0
        elif mode == 'TV interleave' or mode == 1:
            self.settings["mode"] = 1
        else:
            logger.warning(f"Readout mode {mode} is unknown, using default chess pattern.")
            self.settings["mode"] = 0

    def publish_form(self):
        """
        Format the settings in an appropriate way for the AtomS3

        Returns
        -------
        string
            message to publish
        """
        # the rate must become a number between 0 and 7
        conversion = {0.5: 0, 1: 1, 2: 2, 4: 3, 8:4, 16:5, 32:6, 64:7} # TODO: allowed up to 8
        converted = conversion[self.settings["rate"]]
        s, e, m = self.settings["shift"], self.settings["emissivity"], self.settings["mode"]
        string = f"{converted}\n{s}\n{e}\n{m}\n"
        logger.debug(f"Publishing:\n{string}")
        return string

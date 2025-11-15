import math
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.widgets import TextBox
from matplotlib.widgets import RadioButtons
from matplotlib.patches import FancyBboxPatch
from loguru import logger


class ControlPanel:
    """
    Control panel for thermal camera settings

    GUI to manage thermal camera parameters,
    reset pixels and areas, and display the current status of the camera.
    It includes controls for refresh rate, shift, emissivity, and readout mode,
    as well as buttons to apply or reset settings

    Attributes
    ----------
    apply_settings : matplotlib.widgets.Button
        button to apply current settings
    reset_settings : matplotlib.widgets.Button
        button to reset settings to defaults
    get_info : matplotlib.widgets.Button
        button to request current camera settings, pixels and area
    rate_selector : matplotlib.widgets.RadioButtons
        radio buttons to select refresh rate
    mode_selector : matplotlib.widgets.RadioButtons
        radio buttons to select readout mode
    shift_box : matplotlib.widgets.TextBox
        TextBox for shift value
    emissivity_box : matplotlib.widgets.TextBox
        TextBox for emissivity value
    rate_text : matplotlib.text.Text
        shows current refresh rate
    shift_text : matplotlib.text.Text
        shows current shift
    emissivity_text : matplotlib.text.Text
        shows current emissivity

    Methods
    -------
    online()
        Set the camera status display to "ONLINE"
    offline()
        Set the camera status display to "OFFLINE"
    """

    def __init__(self, figsize=(5, 4)):
        self.fig = plt.figure(figsize=figsize)
        self._setup_labels()
        self.reset_pixels, self.reset_area = self._reset_buttons()
        self._settings()
        self._state = self._status_display()
        self._cosmetic_work()

    def _setup_labels(self):
        """ Configure static labels and title
        """
        fig = self.fig
        fig.suptitle("THERMAL CAMERA CONTROL PANEL", fontsize=16, fontweight='bold')
        fig.text(0.125, 0.85, "MLX90640 settings", fontsize=12, fontweight='bold')
        fig.text(0.395, 0.8-0.04, "Current:", fontweight='bold')
        fig.text(0.06, 0.35-0.03, "Readout mode:")
        fig.text(0.725, 0.42,"Status:", fontsize=12, fontweight='bold')

    def _reset_buttons(self):
        """ Configure buttons to reset pixels and area
        """
        r_pix = Button(plt.axes([0.665, 0.68, 0.24, 0.075]), "Reset pixels")
        r_area = Button(plt.axes([0.665, 0.58, 0.24, 0.075]), "Reset area")
        return r_pix, r_area

    def _settings(self):
        """ Configure controls for camera, apply and reset buttons
        """
        fig = self.fig
        # menu for refresh rate
        fig.text(0.1, 0.8-0.02, "Rate [Hz]:")
        self.rate_selector = RadioButtons(plt.axes([0.1, 0.58-0.02, 0.16, 0.2]), (0.5, 1, 2, 4, 8))

        # textboxes for shift and emissivity
        self.shift_box = TextBox(fig.add_axes([0.13, 0.5-0.03, 0.1, 0.07]),
                                 "Shift:", textalignment="center")
        self.emissivity_box = TextBox(fig.add_axes([0.13, 0.4-0.03, 0.1, 0.07]),
                                      "Emis.:", textalignment="center")

        # text to display current settings
        self.rate = fig.text(0.435, 0.65, "...")
        self.shift = fig.text(0.435, 0.495, "...")
        self.emissivity = fig.text(0.425, 0.395, "...")
        self.mode = fig.text(0.415, 0.235, "...")

        # menu for readout mode
        radio_ax = plt.axes([0.05, 0.22-0.03, 0.27, 0.12])
        self.mode_selector = RadioButtons(radio_ax, ('Chess pattern', 'TV interleave'))#, active=0)

        # buttons to apply/reset settings
        self.apply_settings = Button(plt.axes([0.03+0.085, 0.07, 0.14, 0.075]),"APPLY",color="#2589da65")
        self.apply_settings.ax.patch.set_edgecolor("red")
        self.reset_settings = Button(plt.axes([0.27+0.045, 0.07, 0.14, 0.075]), "DEFAULT",color="#2588da65")
        # button to request current settings, pixels and area
        self.get_info = Button(plt.axes([0.66, 0.1, 0.24, 0.075]), "Request info")

    def _status_display(self):
        """ Add display for current camera status (online/offline)
        """
        fig = self.fig
        state = fig.text(0.72, 0.335, "OFFLINE",fontsize=13,color="red",
                bbox=dict(boxstyle="round",
                   ec=(1., 0.5, 0.5),
                   fc=(1., 0.8, 0.8),
                   ))
        return state

    def _cosmetic_work(self):
        """Draw boxes to make it look nicer
        """
        ax_bg = self.fig.add_axes([0, 0, 1, 1], zorder=-10)
        ax_bg.axis("off")
        box_1 = FancyBboxPatch(
            (0.03, 0.03), 0.54, 0.8,
            boxstyle="round,pad=0.0,rounding_size=0.03",
                            fc="#f8f8f8", ec="#cccccc", lw=1.2,
                            transform=ax_bg.transAxes,
                            zorder=-5)
        ax_bg.add_patch(box_1)
        box_2 = FancyBboxPatch(
            (0.37, 0.17), 0.17, 0.57,
            boxstyle="round,pad=0.0,rounding_size=0.03",
                            fc="#f8f8f8", ec="#cccccc", lw=1.2,
                            transform=ax_bg.transAxes,
                            zorder=-5)
        ax_bg.add_patch(box_2)
        box_3 = FancyBboxPatch(
            (0.6+0.025, 0.54), 0.32, 0.25,
            boxstyle="round,pad=0.0,rounding_size=0.03",
                            fc="#f8f8f8", ec="#cccccc", lw=1.2,
                            transform=ax_bg.transAxes,
                            zorder=-5)
        ax_bg.add_patch(box_3)
        box_4 = FancyBboxPatch(
            (0.6+0.025, 0.28), 0.32, 0.2,
            boxstyle="round,pad=0.0,rounding_size=0.03",
                            fc="#f8f8f8", ec="#cccccc", lw=1.2,
                            transform=ax_bg.transAxes,
                            zorder=-5)
        ax_bg.add_patch(box_4)

    def online(self):
        self._state.set_text("ONLINE")
        self._state.set_color("green")
        bbox = self._state.get_bbox_patch()
        bbox.set_facecolor((0.8, 1.0, 0.8))  # light green
        bbox.set_edgecolor((0.5, 1.0, 0.5))  # green border
        self.fig.canvas.draw()

    def offline(self):
        self._state.set_text("OFFLINE")
        self._state.set_color("red")
        bbox = self._state.get_bbox_patch()
        bbox.set_facecolor((1.0, 0.8, 0.8))  # light red
        bbox.set_edgecolor((1.0, 0.5, 0.5))  # red border
        self.fig.canvas.draw()


class CameraSettings:
    """
    Object that contains the camera setings
     
    Attributes
    ----------
    rate : float
        Camera refresh rate in Hz (0.5, 1, 2, 4, 8).
    shift : float
        Shift value (must be positive).
    emissivity : float
        Emissivity coefficient (0 < emissivity <= 1).
    mode : int
        Readout mode: 0 = Chess pattern, 1 = TV interleave.

    Methods
    -------
    default()
        Reset all settings to default values.
    publish_form()
        Format the settings as a string for AtomS3.
    """

    DEFAULTS = {"rate" : 2, "shift" : 8, "emissivity" : 0.95, "mode": 0}

    def __init__(self):
        """Initialize with default values
        """
        self._rate = self.DEFAULTS["rate"]
        self._shift = self.DEFAULTS["shift"]
        self._emissivity = self.DEFAULTS["emissivity"]
        self._mode = self.DEFAULTS["mode"]

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, new_rate):
        """Set new rate

        Parameters
        ----------
        new_rate : float
            refresh rate
        """
        if new_rate in (0.5,1,2,4,8):
            self._rate = new_rate
        else:
            logger.warning(f"{new_rate} is an invalid value for rate")

    @property
    def shift(self):
        return self._shift

    @shift.setter
    def shift(self, new_shift):
        """Set shift

        Parameters
        ----------
        new_shift : float
            shift
        """
        if new_shift >= 0:
            self._shift = new_shift
        else:
            logger.warning(f"{new_shift} is an invalid value for shift (must be positive)")

    @property
    def emissivity(self):
        return self._emissivity

    @emissivity.setter
    def emissivity(self, new_em):
        """Set emissivity

        Parameters
        ----------
        new_em : float
            emissivity, must be between 0 and 1
        """
        if 0<new_em<=1:
            self._emissivity = new_em
        else:
            logger.warning(f"{new_em} is an invalid value for emissivity (must be between 0 and 1)")

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, new_mode):
        """Set readout mode (chess or TV interleave)

        Parameters
        ----------
        mode 
        """
        if new_mode in ('Chess pattern', 0):
            self._mode = 0
        elif new_mode in ('TV interleave', 1):
            self._mode = 1
        else:
            logger.warning(f"Readout mode {new_mode} is unknown, using default chess pattern.")
            self._mode = 0

    def default(self):
        """
        Reset camera settings to default values:
        rate=2 Hz, shift=8, emissivity=0.95, mode=Chess pattern
        """
        self.rate = self.DEFAULTS["rate"]
        self.shift = self.DEFAULTS["shift"]
        self.emissivity = self.DEFAULTS["emissivity"]
        self.mode = self.DEFAULTS["mode"]

    def publish_form(self):
        """
        Format the settings in an appropriate way for the AtomS3

        Return a string representation of the current settings for AtomS3
        The rate is converted to an integer x such that 2^(x-1) = rate, and
        other settings are included as-is.

        Returns
        -------
        string : str
            multiline string with rate, shift, emissivity, and mode.
        """

        r = int(math.log(self._rate, 2)+1)
        s, e, m = self._shift, self._emissivity, self._mode
        string = f"{r}\n{s}\n{e}\n{m}\n"
        logger.debug(f"Publishing:\n{string}")
        return string

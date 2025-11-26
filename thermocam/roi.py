""" 
Define classes for the definition of "interesting" pixels and area, and to handle
the received (through MQTT) data about them.

Constants
---------
MIN_X, MAX_X : int
    Allowed x coordinate bounds.
MIN_Y, MAX_Y : int
    Allowed y coordinate bounds.
"""

from datetime import datetime
import re
import numpy as np
from loguru import logger

MIN_X = 0
MAX_X = 23
MIN_Y = 0
MAX_Y = 31

class InterestingPixels:
    """
    Class to manage the defined pixels.
    
    It stores:
    - the current pixel list,
    - pixel temperature/time data for each one,
    - the Matplotlib "Line2D" object for each pixel

    Pixel coordinates can be defined by the interactions of the user with the GUI,
    or can be parsed from comma-separated "x y" MQTT messages.

    Attributes
    ----------
    p : array-like with shape (N, 2)
        Currently defined pixels.
    pixels_data : dict
        Dictionary mapping (x, y) tuples to dictionary containing time and temperature
        data and Line2D
    """

    def __init__(self):
        self.p = np.empty((0, 2), dtype=int)
        self.pixels_data = {} # will contain the pixel as a key and as a value another dict
                 #  with the times, values and Line2D

    def out_data(self):
        """
        Return a string with the defined pixels' data to be written in output file.

        Data is formatted as follows:
        "(x, y), T" repeated for eache defined pixel and separated by commas
        """
        out = ""
        # loop over data dict
        for key, v in self.pixels_data.items():
            out += f" {key}, {v["temps"][-1]},"
        out = out[:-1] # remove last comma

        return out

    def get_from_str(self, msg):
        """
        Parse current pixels' coordinates from MQTT message. Coordinates already present
        are ignored. Invalid formatting triggers a warning.

        Parameters
        ----------
        msg : str
                received MQTT message as a string
        """

        try:
            current = list(map(str, msg.split(',')))
            # add each pixel
            for i, pixel in enumerate(current):
                coord = list(map(int, pixel.split(' ')))
                if  not np.any(np.all(self.p == coord, axis=1)): # not already present:
                    self.p = np.append(self.p, [[coord[0], coord[1]]], axis=0)
            logger.debug(f"Current pixels: {self.p}")

        except ValueError:
            logger.warning(f"Received pixels have invalid format: {msg}")


    def handle_mqtt(self, msg):
        """
        Update current pixel definition based on received MQTT message.

        If message is "none" pixel definition and data is cleared. Otherwise,
        method get_from_str is called.

        Parameters
        ----------
        msg : str
              received MQTT message as a string
        """

        if msg == "none":
            self.p = np.empty((0, 2), dtype=int)
            self.pixels_data = {}
            logger.info("No pixels are defined.")
        else:
            self.get_from_str(msg)

    def get_from_click(self, x, y):
        """
        Define new pixel from user's mouse click.

        Performs a bound check and, if coordinates are already present, they
        are not appended.

        Parameters
        ----------
        x : int
            x coordinate of the mouse click
        y : int
            y coordinate of the mouse click

        Returns
        -------
        bool
            True if pixel has been added, False otherwise
        """

        if x>MAX_X:
            x = MAX_X
        elif x<MIN_X:
            x = MIN_X
        if y>MAX_Y:
            y = MAX_Y
        elif y<MIN_Y:
            y = MIN_Y
        if  not np.any(np.all(self.p == [(x,y)], axis=1)): # not already present:
            self.p = np.append(self.p, [(x, y)], axis=0)   # append pixel to array
            return True
        return False

    def new_pixel(self):
        """
        Retrieve the last defined pixel and return it in a string format.
        Implemented to make publishing new pixel easier.

        Returns
        -------
        string
            last pixel coordinates formatted as "x y"

        """

        return f"{self.p[-1][0]} {self.p[-1][1]}"


    def update_data(self, msg, ax, t):
        """
        Parse pixel(s) data from message and update live plots.

        Parameters
        ----------
        msg : str
            received MQTT message as a string, containing comma separated "x y T" entries.
        ax : matplotlib.axes.Axes
            Axes on which pixel data is drawn.
        t : datetime
            Timestamp of start time.
        """

        try:
            logger.debug(msg)
            # get current pixels and data from message
            current = [list(map(float, p.split(' '))) for p in msg.split(",")]
            t = (datetime.now() - t).total_seconds()

            # now update value in dictionary or add new one if not present
            for x, y, val in current:
                pixel = (int(x), int(y))
                if pixel not in self.pixels_data: # add to dict and make new line
                    logger.info(f"Receiving new pixel: {pixel}")
                    # create line for its data
                    l, = ax.plot([], [], label=str(pixel), color=np.random.rand(3,))
                    ax.legend(loc="upper left", bbox_to_anchor=(1,1))
                    # add (empty) data and Line2D to dict
                    self.pixels_data[pixel] = {"times": [], "temps": [], "line": l}
                # add values (temperature and time)
                single = self.pixels_data[pixel]
                single["times"].append(t)
                single["temps"].append(val)
                single["line"].set_data(single["times"], single["temps"])

            # update plot axes
            ax.relim()
            ax.autoscale_view()
        except (ValueError, KeyError):
            logger.warning(f"Received pixel data has invalid format: {msg}")



class InterestingArea:
    """
    Class to manage the defined area.
    
    It stores:
    - the current area definition,
    - area temperature/time data,
    - the Matplotlib "Line2D" object for min, max and avg temperature.

    Area can be defined by the interactions of the user with the GUI,
    or can be parsed from MQTT messages.

    
    Attributes
    ----------
    a : array-like with shape (a, 2)
        Currently defined area as (x_left, y_low, width, height).
    area_data : dict
        Dictionary mapping str(self.a) to dictionary containing time and temperature
        data and Line2D
    """

    def __init__(self):
        self.a = np.empty((0, 4),dtype=int)
        self.area_data = {} # will contain the area as a key and as a value another dict with
               # the times, values and Line2D (even though only one area at the time is defined)

    def defined(self):
        """Return whether an area is currently defined.

        Returns
        -------
        bool
            True if an area is defined, False otherwise.       
        """
        return len(self.a)!=0

    def pub_area(self):
        """
        Format the defined area for MQTT publishing.
        It has to be formatted as "x_left y_low w h"

        Returns
        -------
        str
            "x_left y_low w h"
        """

        return f"{self.a[0][0]} {self.a[0][1]} {self.a[0][2]} {self.a[0][3]}" # it's a bit ugly

    def get_from_str(self, msg):
        """
        Parse area definition from MQTT message as x_left, y_low, width, height.
        Invalid formatting triggers a warning and retains the previous area.

        Parameters
        ----------
        msg : str
              received MQTT message as a string
        """

        try:
            # coordinates MUST be integers
            self.a = np.array([list(map(int, msg.split(' ')))], dtype=int)
            # NOTE: self.a is redefined as the new area, it's not appended as in the case of
            #       the pixels: only one area at the time is defined
            logger.info(f"Current area: {self.a}")
        except ValueError:
            logger.warning(f"Received area has invalid format: {msg}, still using previous area")

    def handle_mqtt(self, msg):
        """
        Update current area definition based on received MQTT message.

        If message is "none" area definition and data is cleared. Otherwise,
        method get_from_str is called.

        Parameters
        ----------
        msg : str
              received MQTT message as a string
        """

        if msg == "none":
            logger.info("No area is defined.")
            self.a = np.empty((0, 4),dtype=int)
            self.area_data = {}
        else:
            self.get_from_str(msg)
            logger.debug(f"Current area: {self.a}")

    def get_from_click(self, c):
        """
        Define new area from user's mouse clicks.
        Performs a bounds check.

        Parameters
        ----------
        c : array-like with shape (2, 2)
            contains the coordinates of the two clicked points
        """
        x_left = int(np.min(c, axis=0)[0])
        y_low = int(np.min(c, axis=0)[1])
        w = int(abs(c[0][0] - c[1][0]))+1
        h = int(abs(c[0][1] - c[1][1]))+1

        # sanity checks
        if x_left>MAX_X:
            x_left = MAX_X
        elif x_left<MIN_X:
            x_left = MIN_X
        if y_low>MAX_Y:
            y_low = MAX_Y
        elif y_low<MIN_Y:
            y_low = MIN_Y

        if x_left+w>MAX_X+1:
            w = MAX_X+1-x_left
        if y_low+h>MAX_Y+1:
            h = MAX_Y+1-y_low

        self.a = np.array([(x_left, y_low, w, h)], dtype=int)

    def update_data(self, msg, ax, t):
        """
        Parse area data from received MQTT message and update live plots.
        If received data has invalid format, a warning is triggered.
        
        Parameters
        ----------
        msg : str
              received MQTT message as a string
        ax : matplotlib.axes.Axes
            Axes on which area data is drawn.
        t : datetime
            Timestamp of start time.
        """
        try:
            logger.debug(msg)
            pattern = r'(\w+):\s(-?\d+\.?\d?)'
            matches = re.findall(pattern, msg)
            # Convert to dictionary, converting numbers to float or int
            data = {k: float(v) if "." in v else int(v) for k, v in matches}
            # values should be appended only if they are all present
            if (data["max"] and data["min"] and data["avg"]):
                x = (datetime.now() - t).total_seconds()
                if str(self.a) not in self.area_data:
                    # create 2DLine for min, max and avg
                    l_avg, = ax.plot([], [], color='green', markersize=12, label=r"$T_{avg}$")
                    l_min, = ax.plot([], [], color='blue', markersize=12, label=r"$T_{min}$")
                    l_max, = ax.plot([], [], color='red', markersize=12, label=r"$T_{max}$")
                    if ax.get_legend() is None:
                        ax.legend(loc="upper left", bbox_to_anchor=(1,0.5))
                    self.area_data[str(self.a)] = {"times" : [], "avg" : [], "min" : [], "max" : [],
                                            "l_avg" : l_avg, "l_min" : l_min, "l_max" : l_max}
                # only the currently defined area data is getting updated
                a = self.area_data[str(self.a)]
                a["times"].append(x)
                a["avg"].append(data["avg"])
                a["min"].append(data["min"])
                a["max"].append(data["max"])
                a["l_avg"].set_data(a["times"], a["avg"])
                a["l_min"].set_data(a["times"], a["min"])
                a["l_max"].set_data(a["times"], a["max"])

                # update plot axes
                ax.relim()
                ax.autoscale_view()

        except (TypeError, KeyError):
            logger.warning(f"Received area data has invalid format: {msg}")

    def out_data(self):
        """
        Return a string with the defined area data to be written in output file.

        Data is formatted as follows:
        "x_left, y_low, width, height, avg, min, max"
        """
        x, y, w, h = self.a[0][:]
        a = self.area_data[str(self.a)]

        avg = a["avg"][-1]
        min_T = a["min"][-1]
        max_T = a["max"][-1]
        out = f"{x}, {y}, {w}, {h}, {avg}, {min_T}, {max_T}"
        return out

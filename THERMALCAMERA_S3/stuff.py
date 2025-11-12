from datetime import datetime
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches
from loguru import logger

MIN_X = 0
MAX_X = 23
MIN_Y = 0
MAX_Y = 31

class InterestingPixels:
    """
    Class to define, store and do stuff with the interesting pixels 
    """

    def __init__(self):
        self.p = np.empty((0, 2), dtype=int)
        self.pixels_data = {} # will contain the pixel as a key and as a value another dict
                 #  with the times, values and Line2D

    def __str__(self): # TODO: useless
        s = ""
        for p in self.p:
            s += f"({p[0]}, {p[1]}) "
        return s


    def out_data(self):
        """ Return a string with data to be written in output file
        """
        out = ""
        # loop over data dict
        for key, v in self.pixels_data.items():
            out += f" {key}, {v["temps"][-1]},"
        out = out[:-1] # remove last comma       
        
        return out

    def cleanup(self, scatter):
        """
        Delete previous pixels and data 

        Parameters
        ----------
        scatter : Line2D
                  scatter plot that contains previously defined pixels
        """

        scatter.set_data([], [])
        self.p = np.empty((0, 2), dtype=int)
        self.pixels_data = {}

    def draw_on(self, scatter):
        """
        Add selected pixels to scatter plot
        """

        scatter.set_data(self.p[:,0],self.p[:,1])

    def get_from_str(self, msg):
        """
        If not none, get current pixels

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
            logger.info(f"Current pixels: {self}")
            
        except ValueError:
            logger.warning(f"Received pixels have invalid format: {msg}")


    def handle_mqtt(self, msg, scatter):
        """
        Parameters
        ----------
        msg : str
              received MQTT message as a string
        scatter : Line2D
                    scatter plot to plot selected pixels
        """

        if msg == "none":
            self.cleanup(scatter)
            logger.info("No pixels are defined.")
        else:
            self.get_from_str(msg)

    def get_from_click(self, x, y):
        """
        if coordinates are already present, do not append them
        Also makes sure they are within correct bounds

        Parameters
        ----------
        x : int
        y : int

        Returns
        -------
        bool
            true if pixel has been added
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
            self.p = np.append(self.p, [(x, y)], axis=0)  # append pixel to array
            return True
        else:
            return False
        
    def new_pixel(self):
        """
        Implemented to make publishing new pixel easier

        Returns
        -------
        string
            last pixel coordinates formatted as "x y"

        """

        return f"{self.p[-1][0]} {self.p[-1][1]}"


    def get_data(self, msg, ax, t):
        """
        Get pixel(s) data from message
        """
        # logger.debug(msg)
        try:
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
            logger.warning(f"Received data has invalid format: {msg.payload}")



class InterestingArea:
    """
    Class used to define the interesting area
    """

    def __init__(self):
        self.a = np.empty((0, 4),dtype=int)
        self.area_data = {} # will contain the area as a key and as a value another dict
               #  with the times, values and Line2D (even though only one area at the time is defined)

    def pub_area(self):
        """
        Implemented to make publishing easier: it has to be formatted as
        "x_left y_low w h"
        """

        return f"{self.a[0][0]} {self.a[0][1]} {self.a[0][2]} {self.a[0][3]}" # it's a bit ugly

    def out_data(self):
        """ Return a string with data to be written in output file
        """
        x, y, w, h = self.a[0][:]
        a = self.area_data[str(self.a)]
        
        avg = a["avg"][-1]
        min = a["min"][-1]
        max = a["max"][-1]
        out = f"{x}, {y}, {w}, {h}, {avg}, {min}, {max}"
        return out

    def cleanup(self, ax):
        """
        Delete area drawing from axes

        Parameters
        ----------
        ax : matplotlib Axes
        """

        for p in reversed(ax.patches): # remove previously drawn patches
            p.remove()

    def draw_on(self, ax):
        """
        Draw patch coresponding to selected area

        Parameters
        ----------
        ax : matplotlib Axes
        """
        if self.a.shape[0]>0:
            self.cleanup(ax) # TODO: this has been added to prevent double drawing, but maybe there is a better way
            x_left, y_low, w, h = self.a[0][:]
            rect = patches.Rectangle((x_left-0.5, y_low-0.5), w, h, linewidth=1, edgecolor='b', facecolor='none')
            ax.add_patch(rect)

    def get_from_str(self, msg):
        """
        If not none, get area definition from MQTT message as x_left, y_low, width, height

        Parameters
        ----------
        msg : str
              received MQTT message as a string
        """

        try:
            # coordinates MUST be integers
            self.a = np.array([list(map(int, msg.split(' ')))], dtype=int)
            # NOTE: self.a is redefined as the new area, it's not appended as in the case of the pixels:
            #       this is beacause only one area is defined
            logger.info(f"Current area: {self.a}")
        except ValueError:
            logger.warning(f"Received area has invalid format: {msg}, still using previous area")
            pass

    def handle_mqtt(self, msg, ax):
        """
        Get current area from MQTT message.

        If no area is defined ("none") remove drawing, else (if message can be correctly parsed)
        redefine area and then remove previous drawing

        Parameters
        ----------
        msg : str
              received MQTT message as a string
        ax : matplotlib Axes
        """

        if msg == "none":
            logger.info("No area is defined.")
            self.a = np.empty((0, 4),dtype=int)
            self.area_data = {}
            self.cleanup(ax)
        else:
            self.get_from_str(msg)
            logger.debug(f"Current area: {self.a}")

    def get_from_click(self, c):
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

    def get_data(self, msg, ax, t):
        """
        Get area data from message
        """
        try:
            logger.debug(msg)
            pattern = r'(\w+):\s(-?\d+\.?\d?)'
            matches = re.findall(pattern, msg)
            # Convert to dictionary, converting numbers to float or int automatically
            data = {k: float(v) if "." in v else int(v) for k, v in matches}

            if (data["max"] and data["min"] and data["avg"]): # values should be appended only if they are all present
                x = (datetime.now() - t).total_seconds()
                if str(self.a) not in self.area_data:
                    # create 2DLine for min, max and avg
                    l_avg, = ax.plot([], [], color='green', markersize=12, label=r"$T_{avg}$")
                    l_min, = ax.plot([], [], color='blue', markersize=12, label=r"$T_{min}$")
                    l_max, = ax.plot([], [], color='red', markersize=12, label=r"$T_{max}$")
                    if not hasattr(ax, "_legend"): # TODO: it still shows multiple legends
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
            logger.warning(f"Received data has invalid format: {msg.payload}") 
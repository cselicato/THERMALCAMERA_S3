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

    def cleanup(self, scatter):
        """
        Delete previous pixels

        Parameters
        ----------
        scatter : Line2D
                  scatter plot that contains previously defined pixels
        """

        scatter.set_data([], [])
        self.p = np.empty((0, 2), dtype=int)

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
            logger.debug(f"Current pixels: {self.p}")    # very very ugly
            
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




class InterestingArea:
    """
    Class used to define the interesting area
    """

    def __init__(self):
        self.a = np.empty((0, 4),dtype=int)

    def __str__(self):
        """
        Implemented to make publishing easier: it has to be formatted as
        "x_left y_low w h"
        """

        return f"{self.a[0][0]} {self.a[0][1]} {self.a[0][2]} {self.a[0][3]}" # it's a bit ugly

    def cleanup(self, axes):
        """
        Delete area drawing from axes

        Parameters
        ----------
        ax : matplotlib Axes
        """

        for p in reversed(axes.patches): # remove previously drawn patches
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
    
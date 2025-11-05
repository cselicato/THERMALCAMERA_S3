import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches

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

        current = list(map(str, msg.split(',')))
        # add each pixel
        for i, pixel in enumerate(current):
            coord = list(map(int, pixel.split(' ')))
            # there is no need to check if coord. are already present, if they
            # were they would not have been published
            # TODO: that's not true only if they are published from a terminal 
            self.p = np.append(self.p, [[coord[0], coord[1]]], axis=0)

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
            print("Not looking at anything")
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
            true if pixel has been addes
        """

        if x>MAX_X: 
            x = MAX_X
        elif x<MIN_X:
            x = MIN_X
        if y>MAX_Y: 
            y = MAX_Y
        elif y<MIN_Y:
            y = MIN_Y

        if [(x, y)] not in self.p:
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
        self.a = np.empty((0, 4))   # is this the only way?

    def cleanup(self, axes):
        """
        Empty area array and delete drawing from axes

        Parameters
        ----------
        ax : matplotlib Axes
        """

        for p in reversed(axes.patches): # remove previously drawn patches
            p.remove()
        self.a = np.empty((0, 4), dtype=int)

    def draw_on(self, ax):
        """
        Draw patch coresponding to selected area

        Parameters
        ----------
        ax : matplotlib Axes
        """
        if self.a.shape[0]>0:
            x_left, y_low, w, h = self.a[0][:]; #, self.a[0][1], self.a[0][2], self.a[0][3]
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

        self.a = np.append(self.a, [list(map(int, msg.split(' ')))], axis=0)

    def handle_mqtt(self, msg, ax):
        """
        Parameters
        ----------
        msg : str
              received MQTT message as a string
        ax : matplotlib Axes
        """

        self.cleanup(ax)    # always remove previous area because only one can be defined
        if msg != "none":
            self.get_from_str(msg)

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
        
        self.a = np.append(self.a, [(x_left, y_low, w, h)], axis=0)

    def __str__(self):
        """
        Implemented to make publishing easier: it has to be formatted as
        "x_left y_low w h"
        """

        return f"{self.a[0][0]} {self.a[0][1]} {self.a[0][2]} {self.a[0][3]}" # fa un po' schifo così
    
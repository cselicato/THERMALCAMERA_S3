import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches


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
        # draw selected pixels on image
        scatter.set_data(self.p[:,0],self.p[:,1])

    def get_from_str(self, msg, scatter):
        """
        If not none, get area definition from MQTT message as x_left, y_low, width, height

        Parameters
        ----------
        msg : str
                received MQTT message as a string
        scatter : Line2D
                    scatter plot to plot selected pixels
        """

        current = list(map(str, msg.split(',')))
        # add each pixel
        for i, pixel in enumerate(current):
            coord = list(map(int, pixel.split(' ')))
            # there is no need to check if coord. are already present, if they
            # were they would not have been published
            self.p = np.append(self.p, [[coord[1], coord[0]]], axis=0)

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
        else:
            self.get_from_str(msg, scatter)

    def get_from_click(self, x, y):
        """
        if coordinates are already present, do not append them
        """

        if [(x, y)] not in self.p:
            self.p = np.append(self.p, [(x, y)], axis=0)  # append pixel to array
            return True
        else:
            return False




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
            rect = patches.Rectangle((x_left, y_low), w, h, linewidth=1, edgecolor='b', facecolor='none')
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
        w = int(abs(c[0][0] - c[1][0]))
        h = int(abs(c[0][1] - c[1][1]))
        self.a = np.append(self.a, [(x_left, y_low, w, h)], axis=0)
        print(f"from clicks i got {self.a}")
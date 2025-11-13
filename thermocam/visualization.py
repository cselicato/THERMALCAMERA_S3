import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons


class Display():
    """
    Display to visualize data received from the thermal camera

    On the left, it displays the received thermal image and buttons to take 
    video and select regions of interest.
    On the right, it plots the received pixel(s) and area temperatures.
    """
    def __init__(self, figsize=(10, 5)):
        self._setup_fig(figsize)
        self._create_axes()
        self._init_image()
        self._init_plots()
        self._add_buttons()
        self._add_text()
        self._add_colorbar()

    def _setup_fig(self, figsize):
        """
        Create main figure and subfigures
        """
        self.fig = plt.figure(figsize=figsize)
        gs = self.fig.add_gridspec(1, 2, width_ratios=[0.4, 0.6], wspace=0.15)
        self.img_fig = self.fig.add_subfigure(gs[0])
        self.data_fig = self.fig.add_subfigure(gs[1])
        # get dimensions of fig part that contains the image (only useful part to film)
        box = self.img_fig.bbox
        self.img_dim = (box.x0, self.fig.bbox.height - box.y1, box.width, box.height)
        # clear space for legend and make it look right
        self.data_fig.subplots_adjust(right=0.77, hspace=0.5, top=0.95, bottom=0.1)
        self.img_fig.subplots_adjust(top=0.95, bottom=0.1, right=0.9, left=0.15)

        self.canvas = self.fig.canvas

    def _create_axes(self):
        """
        Create axes for thermal image, pixels data and area data
        """
        self.ax_img = self.img_fig.subplots()
        self.ax_pixels, self.ax_area = self.data_fig.subplots(2, 1)

    def _init_image(self):
        """
        Initialize image visualization
        """

        # Initialize a list of float as per the image data
        self.image = self.ax_img.imshow(np.random.rand(32,24)*30+10, cmap='inferno')
        self.draw_pixel, = self.ax_img.plot([], [], marker='+', color='lime', ms=12, mew=2, linestyle='None')
        # TODO: it would probably make more sense to add methods to this class to update
        #       drawing of pixels and area (currently thst's done by the module roi)
        self.draw_clicks, = self.ax_img.plot([], [], marker='+', color='blue', markersize=12, linestyle='None')

    def _add_text(self):
        """
        Add text labels to image
        """

        self.time_text = self.img_fig.figure.text(0.4*0.05, 0.05, "Waiting for data...")
        self.pix_text = self.data_fig.figure.text(0.45, 0.97, "Waiting for data...")
        self.fig_text = self.fig.figure.text(0.45, 0.48, "Waiting for data...")

    def _add_colorbar(self):
        """
        Add colorbar to thermal image
        """

        cbar = plt.colorbar(self.image, shrink=0.8)
        cbar_ticks = np.linspace(10., 40., num=7, endpoint=True)
        cbar.set_ticks(cbar_ticks)
        cbar.minorticks_on()

        self.cbar = cbar

    def _init_plots(self):
        """
        Initialize pixel and area data visualization
        """
        for ax in [self.ax_pixels, self.ax_area]:
            ax.set_xlabel("Time from start [s]")
            ax.set_ylabel("T [°C]")
            ax.grid(True)
            ax.margins(0.15)

    def _add_buttons(self):
        """ 
        Create buttons to select area and to film video
        """
        self.area_button = CheckButtons(plt.axes([0.4*0.45, 0.9, 0.4*0.3, 0.075]), ['Select area',],
                           [False,], check_props={'color':'red', 'linewidth':1})
        self.video_button = CheckButtons(plt.axes([0.4*0.1, 0.9, 0.4*0.3, 0.075]), ['Video',], [False,],
                          check_props={'color':'green', 'linewidth':1})

    def show(self):
        """
        Show the display
        """
        plt.show()

    def update_cbar(self, min_temp, max_temp):
        """
        Update limits of the plotted colorbar

        Sets lower limit of the colorbar to min and upper limit to max, also
        updates ticks on the colorbar.

        Parameters
        ----------
        min_temp : float
                  minumum measured temperature
        max_temp : float
                  maximum measured temperature
        """

        upper = np.ceil(max_temp + (max_temp - min_temp)*0.1)
        lower = np.floor(min_temp - (max_temp - min_temp)*0.1)

        self.cbar.mappable.set_clim(vmin=lower,vmax=upper)
        ticks = np.linspace(lower, upper, num=10, endpoint=True,)
        self.cbar.set_ticks(ticks)
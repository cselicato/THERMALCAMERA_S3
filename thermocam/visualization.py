import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
from matplotlib import patches


class Display():
    """
    Display to visualize data received from the thermal camera

    On the left, it displays the received thermal image and buttons to take 
    video and select regions of interest.
    On the right, it plots the received pixel(s) and area temperatures.
    """
    def __init__(self, figsize=(10, 5)):
        self._fig = plt.figure(figsize=figsize)
        self.img_fig, self.data_fig, self.canvas = self._setup_fig()
        self._create_axes()
        self._init_image()
        self._init_plots()
        self._add_buttons()
        self._add_text()
        self._cbar = self._add_colorbar()

    def _setup_fig(self):
        """Create subfigures in the main figure

        Returns
        -------
        img_fig
            subfigure for thermal image
        data_fig
            subfigure for plots of live data
        """
        fig = self._fig
        gs = fig.add_gridspec(1, 2, width_ratios=[0.4, 0.6], wspace=0.15)
        img_fig = fig.add_subfigure(gs[0])
        data_fig = fig.add_subfigure(gs[1])

        return img_fig, data_fig, fig.canvas


    def _create_axes(self):
        """
        Create axes for thermal image, pixels data and area data
        """
        gs_img = self.img_fig.add_gridspec(1, 1,left=0.15, right=0.90,top=0.95, bottom=0.10)
        self.ax_img = self.img_fig.add_subplot(gs_img[0])

        gs_data = self.data_fig.add_gridspec(2, 1,top=0.95, bottom=0.10,right=0.77, hspace=0.5
                                             )
        self.ax_pixels = self.data_fig.add_subplot(gs_data[0])
        self.ax_area   = self.data_fig.add_subplot(gs_data[1])

    def _init_image(self):
        """
        Initialize image visualization
        """

        # Initialize a list of float as per the image data
        self.image = self.ax_img.imshow(np.random.rand(32,24)*30+10, cmap='inferno')
        self.draw_pixel, = self.ax_img.plot([], [], marker='+', color='lime', ms=12,
                                            mew=2, linestyle='None')
        self.draw_clicks, = self.ax_img.plot([], [], marker='+', color='blue',
                                             markersize=12, linestyle='None')

    def _add_text(self):
        """
        Add text labels to image
        """

        self.time_text = self.img_fig.figure.text(0.4*0.05, 0.05, "Waiting for data...")
        self.pix_text = self.data_fig.figure.text(0.45, 0.97, "Waiting for data...")
        self.area_text = self.data_fig.figure.text(0.45, 0.48, "Waiting for data...")

    def _add_colorbar(self):
        """
        Add colorbar to thermal image

        Returns
        -------
        cbar
            colorbar
        """

        cbar = plt.colorbar(self.image, shrink=0.8)
        cbar_ticks = np.linspace(10., 40., num=7, endpoint=True)
        cbar.set_ticks(cbar_ticks)
        cbar.minorticks_on()

        return cbar

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
        self.area_button = CheckButtons(plt.axes([0.4*0.45, 0.9, 0.4*0.3, 0.075]),
                ['Select area',],[False,], check_props={'color':'red', 'linewidth':1})
        self.video_button = CheckButtons(plt.axes([0.4*0.1, 0.9, 0.4*0.3, 0.075]),
                ['Video',], [False,],check_props={'color':'green', 'linewidth':1})

    def update_cbar(self, min_temp, max_temp):
        """
        Update limits of the plotted colorbar

        Sets limits of the colorbar according to data max and min,
        with some padding, also updates ticks on the colorbar.

        Parameters
        ----------
        min_temp : float
                  minumum measured temperature
        max_temp : float
                  maximum measured temperature
        """

        upper = np.ceil(max_temp + (max_temp - min_temp)*0.1)
        lower = np.floor(min_temp - (max_temp - min_temp)*0.1)

        self._cbar.mappable.set_clim(vmin=lower,vmax=upper)
        ticks = np.linspace(lower, upper, num=10, endpoint=True,)
        self._cbar.set_ticks(ticks)

    def img_dimensions(self):
        """Return dimensions of fig part that contains the image (only useful part to film)

        Returns
        -------
        img_dim : tuple
            dimensions of thermal image part of the figure
        """

        box = self.img_fig.bbox
        img_dim = (box.x0, self._fig.bbox.height - box.y1, box.width, box.height)
        return img_dim

    def update_pixels(self, pixels):
        """Draw currently defined pixels on thermal image
        """
        self.draw_pixel.set_data(pixels.p[:,0],pixels.p[:,1])

    def update_area(self, area):
        """Draw currently defined area on thermal image
        """
        for p in reversed(self.ax_img.patches): # remove previously drawn patches
            p.remove()
        # if defined, draw current one
        if area.defined():
            x_left, y_low, w, h = area.a[0][:]
            rect = patches.Rectangle((x_left-0.5, y_low-0.5), w, h,
                                     linewidth=1, edgecolor='b', facecolor='none')
            self.ax_img.add_patch(rect)

import struct
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons
from matplotlib import patches
from loguru import logger

class Display():
    """
    Graphical interface for visualizing thermal camera data

    Matplotlib-based interface consisting of two panels: a thermal image view
    (left) and temperature plots (right). It displays in real-time the thermal
    images, the selected pixels and area.It also includes buttons for
    video recording and area selection

    Parameters
    ----------
    figsize : (float, float)
        width, height in inches of the entire figure, default is (10, 5)

    Attributes
    ----------
    ax_img : matplotlib.axes.Axes
        axis displaying the current thermal image
    ax_pixels : matplotlib.axes.Axes
        axis plotting temperatures of selected pixels
    ax_area : matplotlib.axes.Axes
        axis plotting temperatures of a selected rectangular area.
    image : matplotlib.image.AxesImage
        image object containing the thermal frame
    video_button : matplotlib.widgets.CheckButtons
        Checkbox controlling video recording
    area_button : matplotlib.widgets.CheckButtons
        Checkbox enabling area selection mode
    time_text : matplotlib.text.Text
        timestamp of the last received frame
    pix_text : matplotlib.text.Text
        status text for pixel-related information
    area_text : matplotlib.text.Text
        status text for area-related information
    _cbar : matplotlib.colorbar.Colorbar
        Colorbar associated with the thermal image
    """

    def __init__(self, figsize=(10, 5)):
        self._fig = plt.figure(figsize=figsize)
        self._img_fig, self._data_fig, self.canvas = self._setup_fig()
        self.ax_img, self.ax_pixels, self.ax_area = self._create_axes()
        self._init_image()
        self._init_plots()
        self.video_button, self.area_button = self._add_buttons()
        self.time_text, self.pix_text, self.area_text = self._add_text()
        self._cbar = self._add_colorbar()
        self._received = 0 # counter for how many thermal images have been received

    def _setup_fig(self):
        """Create subfigures in the main figure

        Returns
        -------
        img_fig
            subfigure for thermal image
        data_fig
            subfigure for plots of live data
        fig.canvas

        """
        fig = self._fig
        gs = fig.add_gridspec(1, 2, width_ratios=[0.4, 0.6], wspace=0.15)
        img_fig = fig.add_subfigure(gs[0])
        data_fig = fig.add_subfigure(gs[1])

        return img_fig, data_fig, fig.canvas


    def _create_axes(self):
        """_summary_

        Returns
        -------
        ax_img
        ax_pixels
        ax_area
        """
        gs_img = self._img_fig.add_gridspec(1, 1,left=0.15, right=0.90,top=0.95, bottom=0.10)
        ax_img = self._img_fig.add_subplot(gs_img[0])

        gs_data = self._data_fig.add_gridspec(2, 1,top=0.95, bottom=0.10,right=0.77, hspace=0.5
                                             )
        ax_pixels = self._data_fig.add_subplot(gs_data[0])
        ax_area   = self._data_fig.add_subplot(gs_data[1])

        return ax_img, ax_pixels, ax_area

    def _init_image(self):
        """
        Initialize image visualization and scatter plots for pixels and clicks
        """

        # Initialize a list of float as per the image data
        self.image = self.ax_img.imshow(np.random.rand(32,24)*30+10, cmap='inferno')
        self._draw_pixel, = self.ax_img.plot([], [], marker='+', color='lime', ms=12,
                                            mew=2, linestyle='None')
        self._clicks, = self.ax_img.plot([], [], marker='+', color='blue',
                                             markersize=12, linestyle='None')

    def _add_text(self):
        """
        Add text labels to image
        """

        time_text = self._img_fig.figure.text(0.4*0.05, 0.05, "Waiting for data...")
        pix_text = self._data_fig.figure.text(0.45, 0.97, "Waiting for data...")
        area_text = self._data_fig.figure.text(0.45, 0.48, "Waiting for data...")
        return time_text, pix_text, area_text

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
        Set axes labels for pixel and area data visualization
        """
        for ax in [self.ax_pixels, self.ax_area]:
            ax.set_xlabel("Time from start [s]")
            ax.set_ylabel("T [°C]")
            ax.grid(True)
            ax.margins(0.15)

    def _add_buttons(self):
        """ 
        Create buttons to select area and to film video
        
        Returns
        -------
        video_button : matplotlib.CheckButtons
        area_button : matplotlib.CheckButtons
        """
        video_button = CheckButtons(plt.axes([0.4*0.1, 0.9, 0.4*0.3, 0.075]),
            ['Video',], [False,],check_props={'color':'green', 'linewidth':1})        
        area_button = CheckButtons(plt.axes([0.4*0.45, 0.9, 0.4*0.3, 0.075]),
            ['Select area',],[False,], check_props={'color':'red', 'linewidth':1})
        
        return video_button, area_button

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
        """Return the dimensions of the thermal image region of the figure
         
        This is useful for capturing the video, since this is the only useful part
        to film

        Returns
        -------
        img_dim : tuple of float
            dimensions of thermal image part of the figure
        """

        box = self._img_fig.bbox
        img_dim = (box.x0, self._fig.bbox.height - box.y1, box.width, box.height)
        return img_dim

    def draw_clicks(self, c):
        """Plot clicked points used to define interesting area on thermal image

        Parameters
        ----------
        c : array-like with shape (n, 2)
            coordinates of the clicked points
        """
        self._clicks.set_data(c[:,0],c[:,1])

    def update_image(self, msg):
        """
        Update the displayed thermal image from an incoming MQTT message

        The message payload is expected to contain 768 float32 temperature
        values. The frame is reshaped, transposed, and then drawn.
        Every ten frames, the colorbar limits are automatically updated based
        on the current minimum and maximum temperatures (with 10% padding).

        Parameters
        ----------
        msg : received MQTT message as-is

        Raises
        ------
        struct.error
            if the payload size is invalid for unpacking
        ValueError
            if the reshaped array does not match the expected format
        """
        try:
            flo_arr = [struct.unpack('f', msg.payload[i:i+4])[0]
                       for i in range(0, len(msg.payload), 4)]
            # data must be transposed to match what is shown on AtomS3 display
            thermal_img = np.array(flo_arr).reshape(24,32).T
            self.image.set_data(thermal_img)

            self.time_text.set_text(datetime.now().strftime("%d/%m/%Y, %H:%M:%S"))
            self.canvas.draw() # draw canvas

            if self._received%10 == 0:
                # update colorbar according to min and max of the measured temperatures
                self.update_cbar(np.min(thermal_img), np.max(thermal_img))

            self._received += 1

        except (struct.error, ValueError) as e:
            logger.warning(f"Received invalid image: {e}")

    def update_pixels(self, pixels):
        """Draw currently defined pixels on thermal image

        Parameters
        ----------
        pixels : thermocam.c.InterestingPixels
        """
        self._draw_pixel.set_data(pixels.p[:,0],pixels.p[:,1])

    def update_area(self, area):
        """Draw a rectangle around the currently defined area on thermal image

        The previous area is removed before drawing new one

        Parameters
        ----------
        area : thermocam.roi.InterestingArea
        """
        for p in reversed(self.ax_img.patches): # remove previously drawn patches
            p.remove()
        # if defined, draw current one
        if area.defined():
            x_left, y_low, w, h = area.a[0][:]
            rect = patches.Rectangle((x_left-0.5, y_low-0.5), w, h,
                                     linewidth=1, edgecolor='b', facecolor='none')
            self.ax_img.add_patch(rect)

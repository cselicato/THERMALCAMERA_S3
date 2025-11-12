from datetime import datetime
import numpy as np
import cv2
from loguru import logger

from THERMALCAMERA_S3 import THERMALCAMERA_S3_VIDEO


class VideoMaker:
    """
    Class used to save a video of the plot
    """

    def __init__(self, size=(720,960), fps=4):
        self.filming = False
        self.size = size
        self.fps = fps

    def start_video(self):
        """
        Create a VideoWriter object

        Parameters
        ----------
        none
        """

        now = datetime.now() # current date and time
        time = now.strftime("%Y%m%d_%H%M%S")
        
        filename = THERMALCAMERA_S3_VIDEO / f"{time}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video = cv2.VideoWriter(filename, fourcc, self.fps, self.size, isColor=True)
        self.filming = True
        logger.info(f"Filming {filename}")

    def add_frame(self, fig, bbox_inches=None):
        """
        Add frame to video if filming, else do nothing
    
        Parameters
        ----------
        fig : matplotlib.figure.Figure
              main figure
        bbox_inches : tuple (x0, y0, width, height)
            optional, bounding box (in display coordinates) for the region to record
        """
        if not self.filming:
            return
    
        
        data_arr = np.asarray(fig.canvas.renderer.buffer_rgba()) # convert to RGBA array
    
        if bbox_inches is not None:
            x0, y0, width, height = bbox_inches
            # Clip and convert to int
            x0, y0, width, height = map(int, [x0, y0, width, height])
            data_arr = data_arr[y0:y0+height, x0:x0+width, :]
    
        data_arr = cv2.cvtColor(data_arr, cv2.COLOR_RGBA2BGR) # Convert to BGR (opencv's default)
        data_arr = cv2.resize(data_arr, self.size)
    
        self.video.write(data_arr)


    def stop_video(self):
        """
        Save output video

        Parameters
        ----------
        none
        """

        self.video.release()
        self.filming = False
        logger.info(f"Stopped filming, saved output video")


"""
Define the video-recording object to save Matplotlib figures as mp4 files.
"""

from datetime import datetime
import numpy as np
import cv2
from loguru import logger

from thermocam import THERMOCAM_VIDEO


class VideoMaker:
    """
    Class for creating mp4 videos from Matplotlib figure frames.

    Uses cv2.VideoWriter object and provides methods to: start video, add frame,
    stop video and save the output (stored in the directory defined by
    "thermocam.THERMOCAM_VIDEO"). The video is timestamped with the start time.

    Parameters
    ----------
    size : tuple of int, default: (720, 960)
        Output video size in pixels
    fps : int, default: 4
        Frame rate of the output video.

    Attributes
    ----------
    filming : bool
        Whether recording is currently active.
    size : tuple of int
        Output video size in pixels.
    fps : int
        Output video framerate.
    video : cv2.VideoWriter
        Video writer object.
    """

    def __init__(self, size=(720,960), fps=4):
        self.filming = False
        self.size = size
        self.fps = fps

    def start_video(self):
        """
        Initialize a new video file for recording.

        Creates a timestamped mp4 file in the directory defined by
        "thermocam.THERMOCAM_VIDEO" and creates a cv2.VideoWriter object.

        Parameters
        ----------
        none
        """

        now = datetime.now() # current date and time
        time = now.strftime("%Y%m%d_%H%M%S")

        filename = THERMOCAM_VIDEO / f"{time}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video = cv2.VideoWriter(filename, fourcc, self.fps, self.size, isColor=True)
        self.filming = True
        logger.info(f"Filming {filename}")

    def add_frame(self, fig, bbox_inches=None):
        """
        Add frame from Matplotlib figure to video if filming=True, else do nothing
    
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
        Finalize and close the video file, set filming = False.

        Parameters
        ----------
        none
        """

        self.video.release()
        self.filming = False
        logger.info("Stopped filming, saved output video")

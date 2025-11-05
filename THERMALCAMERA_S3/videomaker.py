from datetime import datetime
import numpy as np
import cv2

from THERMALCAMERA_S3 import THERMALCAMERA_S3_DIS_VIDEO
from THERMALCAMERA_S3 import THERMALCAMERA_S3_PIX_VIDEO
from THERMALCAMERA_S3 import THERMALCAMERA_S3_AREA_VIDEO


class VideoMaker:
    """
    Class used to save a video of the plot
    """

    def __init__(self, what_kind, size=(720,960), fps=4):
        self.filming = False
        self.size = size
        self.fps = fps
        self.what_kind = what_kind
        if (what_kind=="display"):
            self.outpath = THERMALCAMERA_S3_DIS_VIDEO
        elif (what_kind=="pixel"):
            self.outpath = THERMALCAMERA_S3_PIX_VIDEO
        elif (what_kind=="area"):
            self.outpath = THERMALCAMERA_S3_AREA_VIDEO
        else:
            raise ValueError(f"Unknown what_kind: {what_kind}")
    def start_video(self):
        """
        Create a VideoWriter object

        Parameters
        ----------
        none
        """

        now = datetime.now() # current date and time
        time = now.strftime("%d_%m_%Y__%H_%M_%S")
        
        filename = self.outpath/f"{time}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video = cv2.VideoWriter(filename, fourcc, self.fps, self.size, isColor=True)
        self.filming = True
        print(f"Filming {filename}")

    def add_frame(self, fig):
        """
        Add frame to video if filming, else do nothing

        Parameters
        ----------
        fig : figure
        """

        if self.filming:
            data_arr = np.asarray(fig.canvas.renderer.buffer_rgba())
            data_arr = cv2.cvtColor(data_arr, cv2.COLOR_RGBA2BGR) # Convert to BGR (opencv's default)
            data_arr = cv2.resize(data_arr, self.size) # resize image to video size
            self.video.write(data_arr) # add image to video writer
        else:
            pass

    def stop_video(self):
        """
        Save output video

        Parameters
        ----------
        none
        """

        self.video.release()
        self.filming = False
        print(f"Stopped filming, saved output video")


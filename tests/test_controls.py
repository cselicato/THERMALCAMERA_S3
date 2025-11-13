"""
Test for module controls
"""

import matplotlib.pyplot as plt

from thermocam.controls import ControlPanel, CameraSettings


def test_panel():
    """
    Look at it 
    """

    panel = ControlPanel()
    
    panel.rate.set_text("is")
    panel.shift.set_text("it")
    panel.emissivity.set_text("working?")
    panel.fig.canvas.draw()
    plt.show()


def test_camerasettings():
    """
    I'll think about something
    """

    s = CameraSettings()

test_panel()
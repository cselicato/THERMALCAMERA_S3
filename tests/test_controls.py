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

    panel.rate.set_text("1")
    panel.shift.set_text("9")
    panel.emissivity.set_text("0.95")
    panel.mode.set_text("TV")

    panel.online()
    panel.fig.canvas.draw()


def test_camerasettings():
    """
    Check values are set correctly
    """

    s = CameraSettings()

    s.rate = 8
    s.emissivity = 0.6
    s.shift = 10
    s.mode = 1

    assert s.rate== 8, "Not setting rate value correctly"
    assert s.emissivity== 0.6, "Not setting emissivity value correctly"
    assert s.shift== 10, "Not setting shift value correctly"
    assert s.mode== 1, "Not setting mode value correctly"
    s.publish_form()

    s.default()
    assert s.rate== 2, "Not setting default rate value correctly"
    assert s.emissivity== 0.95, "Not setting default emissivity value correctly"
    assert s.shift== 8, "Not setting default shift value correctly"
    assert s.mode== 0, "Not setting default mode value correctly"

    s.publish_form()

if __name__ == "__main__":
    test_camerasettings()
    test_panel()

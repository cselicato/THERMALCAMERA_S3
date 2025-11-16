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
    plt.show()


def test_camerasettings():
    """
    Check values are set correctly
    """

    s = CameraSettings()

    # the following should give no issues
    s.rate = 8
    s.emissivity = 0.6
    s.shift = 10
    s.mode = 1

    assert s.rate== 8, "This shouldn't give errors"
    assert s.emissivity== 0.6, "This shouldn't give errors"
    assert s.shift== 10, "This shouldn't give errors"
    assert s.mode== 1, "This shouldn't give errors"
    s.publish_form()

    s.default()
    assert s.rate== 2, "This shouldn't give errors"
    assert s.emissivity== 0.95, "This shouldn't give errors"
    assert s.shift== 8, "This shouldn't give errors"
    assert s.mode== 0, "This shouldn't give errors"

    s.publish_form()

if __name__ == "__main__":
    test_camerasettings()
    test_panel()

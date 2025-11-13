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

    panel.state.set_text("HELLOO :)")
    panel.fig.canvas.draw()
    plt.show()


def test_camerasettings():
    """
    I'll think about something
    """

    s = CameraSettings()

    # the following should give no issues
    s.set_rate(8)
    s.set_em(0.6)
    s.set_shift(10)
    s.set_readout(1)

    assert s.settings["rate"]== 8, "This shouldn't give errors"
    assert s.settings["emissivity"]== 0.6, "This shouldn't give errors"
    assert s.settings["shift"]== 10, "This shouldn't give errors"
    assert s.settings["mode"]== 1, "This shouldn't give errors"
    

    s.default()
    assert s.settings["rate"]== 2, "This shouldn't give errors"
    assert s.settings["emissivity"]== 0.95, "This shouldn't give errors"
    assert s.settings["shift"]== 8, "This shouldn't give errors"
    assert s.settings["mode"]== 0, "This shouldn't give errors"

test_panel()
test_camerasettings()

"""
Test for module visualization
"""

import numpy as np
import matplotlib.pyplot as plt

from thermocam.visualization import Display

class FakeMsg:
    """Object with payload method to mimick real MQTT message
    """
    def __init__(self, payload):
        self.payload = payload

def test_display():
    """
    Show the display panel. It should have some clear space on the
    right to show the legends of the plotted pixels and area.
    """

    fig = Display()

    fig.time_text.set_text("Hello world!")
    fig.pix_text.set_text("Hello world!")
    fig.area_text.set_text("Hello world!")

    # generate random image
    values = np.random.rand((32*24))
    values = np.float32(values)
    payload = values.tobytes()
    msg = FakeMsg(payload)

    fig.update_image(msg)

    plotted = fig.image.get_array()
    assert (plotted==values.reshape(24,32).T).all(),"It's not plotting the right values"
    plt.show()

if __name__ == "__main__":
    test_display()

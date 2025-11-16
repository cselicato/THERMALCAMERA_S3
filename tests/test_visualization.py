"""
Test for module visualization
"""

import matplotlib.pyplot as plt

from thermocam.visualization import Display


def test_display():
    """
    Show the display panel. It should have some clear space on the
    right to show the legends of the plotted pixels and area.
    """

    fig = Display()

    fig.time_text.set_text("Hello world!")
    fig.pix_text.set_text("Hello world!")
    fig.area_text.set_text("Hello world!")

    plt.show()

if __name__ == "__main__":
    test_display()

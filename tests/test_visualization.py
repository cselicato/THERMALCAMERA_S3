"""
Test for module visualization
"""

import matplotlib.pyplot as plt

from thermocam.visualization import Display


def test_display():
    """
    Look at it 
    """

    fig = Display()
    plt.show()

if __name__ == "__main__":
    test_display()

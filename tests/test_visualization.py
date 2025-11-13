"""
Test for module controls
"""

import matplotlib.pyplot as plt

from thermocam.visualization import Display


def test_display():
    """
    Look at it 
    """

    fig = Display()
    fig.show()
    
test_display()
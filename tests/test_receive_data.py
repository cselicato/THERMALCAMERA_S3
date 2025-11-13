"""
Test script receive_data.py
"""

import ast
import matplotlib.pyplot as plt
import struct
import numpy as np
import paho.mqtt.client as mqtt
from loguru import logger


MQTT_SERVER = "test.mosquitto.org"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(MQTT_SERVER, 1883, 60)

# the idea is:
# get saved image from file and publish it (in the same format
# the AtomS3 would)
# then check if receive_data plots the expected thing
# where check means look at it
# a similar thing could be done for the other data 
def test_thermal_img():

    # get saved image
    with open("tests/image.txt") as file:
        lines = [line.rstrip() for line in file]

    data = ast.literal_eval(lines[0])
    flo_arr = [struct.unpack('f', data[i:i+4])[0] 
               for i in range(0, len(data), 4)]
    
    thermal_img = np.array(flo_arr).reshape(24,32).T
    fig, ax = plt.subplots()
    im = ax.imshow(thermal_img, cmap='inferno')
    plt.show()

test_thermal_img()
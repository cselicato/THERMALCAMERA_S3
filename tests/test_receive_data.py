"""
Test script receive_data.py

Usage: run this script and then run receive_data to visually check
it plots what expected
"""

import ast
import time
import paho.mqtt.client as mqtt
from loguru import logger

# MQTT_SERVER = "test.mosquitto.org"
MQTT_SERVER = "broker.emqx.io"

class DummyCamera:
    """
    Generate and publish data that mimics what the AtomS3 publishes
    """

    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.connect(MQTT_SERVER, 1883, 60)

    def pixel_data(self):
        """ Publish pixel data
        """
        self.client.publish("/singlecameras/camera1/pixels/data", "1 2 3.00,4 5 6.00")

    def area_data(self):
        """ Publish area data
        """
        self.client.publish("/singlecameras/camera1/area/data", "max: 10 min: 9 avg: 8 x: 7 y: 6 w: 5 h: 4")

    def image(self):
        """ Publish image
        """
        with open("tests/image.txt") as file:
            lines = [line.rstrip() for line in file]
        img = ast.literal_eval(lines[0])
        self.client.publish("/singlecameras/camera1/image", img)


def manual_test_loop():
    camera = DummyCamera()

    logger.info("Starting dummy camera publish loop. Press CTRL+C to stop.")
    try:
        while True:
            time.sleep(0.5)
            camera.pixel_data()
            camera.area_data()
            camera.image()
    except KeyboardInterrupt:
        logger.info("Stopped by user.")


if __name__ == "__main__":
    manual_test_loop()

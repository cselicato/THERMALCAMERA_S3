"""
Script to receive and plot the thermocamera data sent by the AtomS3 
"""

import argparse
import sys
import time
import matplotlib.pyplot as plt
import paho.mqtt.client as mqtt
from loguru import logger

from thermocam.handler import ThermoHandler
from thermocam.callbacks import MQTTCallbacks


# MQTT_SERVER = "test.mosquitto.org"
MQTT_SERVER = "broker.emqx.io" # TODO: find a way to write server path in a config file
                               # or something similar

def level_filter(levels):
    """
    Filter function for Loguru that allows only specified levels.

    Parameters
    ----------
    levels : list[str]
        Log level names to include

    Returns
    -------
    callable
        Function usable as Loguru's `filter` argument.
    """
    def is_level(record):
        return record["level"].name in levels
    return is_level


def main():
    logger.remove(0)
    logger.add(sys.stderr, filter=level_filter(["WARNING", "ERROR", "INFO"]))

    parser = argparse.ArgumentParser(description="Receive data from thermal camera")
    parser.add_argument("--save", default="y",choices=["y", "n"], help="Save output txt files with"
                        "pixels data and area data")

    args = parser.parse_args()
    save = True if args.save == "y" else False

    handler = ThermoHandler(save)
    mqtt_cbs = MQTTCallbacks(handler)

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.on_connect = mqtt_cbs.on_connect
        client.on_message = mqtt_cbs.on_message
        client.connect(MQTT_SERVER, 1883, 60)

        handler.client = client

        client.publish("/singlecameras/camera1/info_request", "1")
        time.sleep(0.5)
        client.loop_start()
        plt.show()

    except OSError as e:
        if e.errno == 101:
            logger.error("Network is unreachable, check internet connection or try later :(")
        else:
            logger.error(f"Connection failed: {e}")
    except KeyboardInterrupt:
        plt.close("all")
        logger.info("Shutting down...")
    finally:
        client.loop_stop()
        client.disconnect()
        handler.close_files()


if __name__ == "__main__":
    main()

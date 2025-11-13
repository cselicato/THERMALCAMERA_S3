"""
    Script to send from command line camera settings to AtomS3
"""

import argparse
import paho.mqtt.client as mqtt
from thermocam.controls import CameraSettings
from loguru import logger

def valid_em(v):
    val = float(v)
    if not 0. < val <= 1.:
        raise argparse.ArgumentTypeError(f"{v} is an invalid value, must be between 0 and 1")
    return val


def main():
    parser = argparse.ArgumentParser(description="Send thermal camera MLX90640 setting to AtomS3 from the command line")

    parser.add_argument("--host", default="test.mosquitto.org", help="MQTT broker hostname (default: test.mosquitto.org)")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port (default: 1883)")

    parser.add_argument("--rate", type=float,choices=[0.5, 1, 2, 4, 8], default=2., help="Thermal camera refresh rate in Hz (default is 2 Hz)")
    parser.add_argument("--shift", type=float, default=8, help="Shift for ambient temperature (default shift for MLX90640 in open air is 8)")
    parser.add_argument("--emissivity", type=valid_em, default=0.95, help="Emissivity of the observed object, used to correct the temperature (default is 0.95). Must be a float between 0 and 1")
    parser.add_argument("--mode", type=float,choices=[0, 1], default=0, help="Readout mode: 0 for chess pattern (default), 1 for TV interleave")

    args = parser.parse_args()

    settings = CameraSettings()

    settings.set_rate(args.rate)
    settings.set_shift(args.shift)
    settings.set_em(args.emissivity)
    settings.set_readout(args.mode)

    # connect to MQTT
    logger.info("Connecting to MQTT server")
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect(args.host, args.port, 60)

        # Publish message
        result = client.publish("/singlecameras/camera1/settings", settings.publish_form(), retain=args.retain)
        result.wait_for_publish()

        logger.info("Published")

        client.disconnect()
    except OSError as e:
        if e.errno == 101:
            logger.error("Network is unreachable, check internet connection or try later :(")
        else:
            logger.error(f"Connection failed: {e}")

if __name__ == "__main__":
    main()
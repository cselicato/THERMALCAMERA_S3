# thermocam

A project to visualize and record thermal camera data from a MLX90640 sensor connected to a M5Stack AtomS3, which publishes data to a MQTT broker.

This repository contains:
- thermocam Python package
- Scripts:
    - receive_data.py
    - send_settings.py
- therm_atom folder: contains the AtomS3 sketch therm_atom.ino, along with the necessary libraries to process the data from the MLX90640 sensor

Usage
Preliminary steps:
- Before uploading the sketch to the AtomS3, modify Wi-Fi SSID, password, and MQTT server address to the desired values. The default MQTT server is test.mosquitto.org, which is public and free to use
(and requires no authentication)
- install the thermocam package
- modify the scrips receive_data.py and send_settings.py to insert the same MQTT server inserted in the sketch 

Then, with the AtomS3 active and connected, launching the script receive_data allows the user to receive and visualize the data.
It also allows the user to:
- define pixels of interest by clicking on the thermal image (the AtomS3 will memorize these pixels and publish their temperature) and (if "select area" checkbox is selected) to define the area of interest (similarly to the pixels, the AtomS3 will publish its maximum, minimum and average temperature)
- save txt files taht contain the data of the defined regions of interest
- save a video of the thermal image

A control panel opens together with the visualization window. It allows the user to:
- configure the MLX90640 settings (refresh rate, shift, emissivity and readout mode) by interacting with the GUI
- upon clicking the APPLY button, the desired settings are published. When the AtomS3 receives them, it writes the settings to a file and then reboots, initializing the camera with the stored parameters
- upon clicking the DEFAULT button, it publishes the default settings, and the AtomS3 proceeds as above.
- Monitor the current settings
- reset pixels and area by clicking the relative buttons
- the button "request info" sends a message that, when received bt the AtomS3, triggers the publishing of the current settings, pixels and area. This is useful because these values should be retained via persistent MQTT messages, but the broker may fail to deliver them reliably.
- Monitor the current state of the AtomS3: ONLINE if a thermal frame has been received in the last 2 seconds, OFFLINE otherwise


The script send_settings.py allows the user to send the camera setting from the terminal, without needing to interact with the GUI.

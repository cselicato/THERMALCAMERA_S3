import paho.mqtt.client as mqtt
import struct
# MQTT_SERVER = "pccmslab1"
MQTT_SERVER = "test.mosquitto.org"
# MQTT_PATH = "/ar/thermal/image"
MQTT_PATH = "/singlecameras/camera1/image"

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

import matplotlib.animation as animation
import cv2

# Initialize a list of float as per your data. Below is a random example
fig, ax = plt.subplots()
im = ax.imshow(np.random.rand(24,32)*30+10)
#plt.show()
#im = ""
#plt.ion()
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_PATH)
    # The callback for when a PUBLISH message is received from the server.


def on_message(client, userdata, msg):
    global im
    # more callbacks, etc
    # Create a file with write byte permission
    print(msg.payload)
    print(len(msg.payload))
    flo_arr = [struct.unpack('f', msg.payload[i:i+4])[0] for i in range(0, len(msg.payload), 4)]
    print(flo_arr)
    if im == "" :
        plt.figure(figsize=(10,8))
        im = plt.imshow(np.array(flo_arr).reshape(24,32), cmap='inferno', interpolation='nearest', norm=LogNorm())
        plt.colorbar()
    #    plt.savefig('img.png', dpi = 300)
        plt.draw()
    else:
        im.set_data(np.array(flo_arr).reshape(24,32))
        plt.draw()

    #plt.show()
#    img = cv2.imread('img.png')
#    resized_img = cv2.resize(img, (320,240))
#    cv2.imwrite('img.png', resized_img)

# The callback for when the client receives a CONNACK response from the server.


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_SERVER, 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
#client.loop_forever()
client.loop_start()
plt.show()

"""web socket driver for tom's home built weather station"""

import math
import time
import paho.mqtt.client as mqtt
import json
import weewx.drivers
import weeutil.weeutil
import logging
from queue import Queue

DRIVER_NAME = 'ESP32MQTT'
DRIVER_VERSION = "1.0"

log = logging.getLogger(__name__)

def loader(config_dict, engine):

    #start_ts, resume_ts = extract_starts(config_dict, DRIVER_NAME)

    stn = ESP32Mqtt(**config_dict[DRIVER_NAME])

    return stn


class ESP32Mqtt(weewx.drivers.AbstractDevice):
    """ESP32 Mqtt start """

    def __init__(self, **stn_dict):
        self.mqtt_host = stn_dict.get('mqtt_host', 'weewx01.internal')
        self.mqtt_topic = stn_dict.get('mqtt_topic', 'esp32_weather_feed')
        self.queue = Queue()
        self.mqttc = mqtt.Client()
        self.mqttc.on_connect = self.on_connect
        self.mqttc.on_message = self.on_message
        self.mqttc.connect(self.mqtt_host)
        self.mqttc.loop_start()
        log.info("starting driver mqtt thread")

    def process_packet(self, message):
        _packet = {'dateTime': int(time.time()),
                    'usUnits' : weewx.US }
        _packet['outTemp'] = message['remote']['temp']
        _packet['outHumidity'] = message['remote']['humidity']
        _packet['inTemp'] = message['local']['temp']
        _packet['inHumidity'] = message['local']['humidity']
        _packet['pressure'] = message['local']['pressure']
        _packet['windSpeed'] = message['remote']['avg_wind']
        _packet['windGust'] = message['remote']['gust_wind']
        _packet['windDir'] = message['remote']['wind_dir']
        _packet['rain'] = message['remote']['rainbuckets']
        _packet['supplyVoltage'] = message['remote']['battery']
        return _packet

    def on_connect(self, client, userdata, flags, reason_code):
        #if reason_code.is_failure:
        #    print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
        #else:
        #    # we should always subscribe from on_connect callback to be sure
            # our subscribed is persisted across reconnections.
        client.subscribe(self.mqtt_topic)

    def on_message(self, client, userdata, message):
        self.queue.put(message.payload)

    def genLoopPackets(self):
        while True:
            raw_message = self.queue.get()
            try:
                message = json.loads(raw_message)
            except TypeError:
                print(f"failed decode json, raw dump: {raw_message}")
                continue

            packet = self.process_packet(message)
            yield packet

    @property
    def hardware_name(self):
        return "ESP32MQTT"


def confeditor_loader():
    return ESP32MqttConfEditor()

class ESP32MqttConfEditor(weewx.drivers.AbstractConfEditor):
    @property
    def default_stanza(self):
        return """
[ESP32Mqtt]
    # This section is for the weewx ESP32 Mqtt driver

    # The websocket url to connect to
    mqtt_host = localhost

    # The topic containing the weather data
    mqtt_topic = esp32_weather_feed

    # The driver to use:
    driver = weewx.drivers.esp32_mqtt
"""


if __name__ == "__main__":
    station = ESP32Mqtt()
    for packet in station.genLoopPackets():
        print(weeutil.weeutil.timestamp_to_string(packet['dateTime']), packet)

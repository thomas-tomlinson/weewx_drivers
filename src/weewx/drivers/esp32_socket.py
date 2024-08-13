"""web socket driver for tom's home built weather station"""

import math
import time
import websocket
import json
import weewx.drivers
import weeutil.weeutil

DRIVER_NAME = 'ESP32SOCKET'
DRIVER_VERSION = "1.0"


def loader(config_dict, engine):

    #start_ts, resume_ts = extract_starts(config_dict, DRIVER_NAME)

    stn = ESP32Socket(**config_dict[DRIVER_NAME])

    return stn


class ESP32Socket(weewx.drivers.AbstractDevice):
    """ESP32 Socket start """

    def __init__(self, **stn_dict):
        self.ws_url = stn_dict.get('host_url', 'ws://weather-receive.localdomain:5000/weather_stream')

#        self.observations = {
#            'outTemp'    : Observation(magnitude=20.0,  average= 50.0, period=24.0, phase_lag=14.0, start=start_ts),
#            'inTemp'     : Observation(magnitude=5.0,   average= 68.0, period=24.0, phase_lag=12.0, start=start_ts),
#            'barometer'  : Observation(magnitude=1.0,   average= 30.1, period=48.0, phase_lag= 0.0, start=start_ts),
#            'pressure'   : Observation(magnitude=1.0,   average= 30.1, period=48.0, phase_lag= 0.0, start=start_ts),
#            'windSpeed'  : Observation(magnitude=5.0,   average=  5.0, period=48.0, phase_lag=24.0, start=start_ts),
#            'windDir'    : Observation(magnitude=180.0, average=180.0, period=48.0, phase_lag= 0.0, start=start_ts),
#            'windGust'   : Observation(magnitude=6.0,   average=  6.0, period=48.0, phase_lag=24.0, start=start_ts),
#            'windGustDir': Observation(magnitude=180.0, average=180.0, period=48.0, phase_lag= 0.0, start=start_ts),
#            'outHumidity': Observation(magnitude=30.0,  average= 50.0, period=48.0, phase_lag= 0.0, start=start_ts),
#            'inHumidity' : Observation(magnitude=10.0,  average= 20.0, period=24.0, phase_lag= 0.0, start=start_ts),
#            'radiation'  : Solar(magnitude=1000, solar_start=6, solar_length=12),
#            'UV'         : Solar(magnitude=14,   solar_start=6, solar_length=12),
#            'rain'       : Rain(rain_start=0, rain_length=3, total_rain=0.2, loop_interval=self.loop_interval),
#            'txBatteryStatus': BatteryStatus(),
#            'windBatteryStatus': BatteryStatus(),
#            'rainBatteryStatus': BatteryStatus(),
#            'outTempBatteryStatus': BatteryStatus(),
#            'inTempBatteryStatus': BatteryStatus(),
#            'consBatteryVoltage': BatteryVoltage(),
#            'heatingVoltage': BatteryVoltage(),
#            'supplyVoltage': BatteryVoltage(),
#            'referenceVoltage': BatteryVoltage(),
#            'rxCheckPercent': SignalStrength()}

    #def process_time(self, timestring):
    #    time_struct = time.strptime(timestring, "%Y-%m-%dT%H:%M:%SZ") 


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

    def genLoopPackets(self):
        #ws = websocket.WebSocketApp(self.ws_url,
        #                            on_message=self.process_packet,
        #                            )
        ws = websocket.WebSocket()
        ws.connect(self.ws_url)
        while True:
            raw_message = ws.recv()
            try:
                message = json.loads(raw_message)
            except Exception as e:
                print("failed to load data read over socket")
                continue

            packet = self.process_packet(message)
            yield packet
#        while True:
#
#            _packet = {'dateTime': int(self.the_time+0.5),
#                       'usUnits' : weewx.US }
#            for obs_type in self.observations:
#                _packet[obs_type] = self.observations[obs_type].value_at(avg_time)
#            yield _packet

    @property
    def hardware_name(self):
        return "ESP32SOCKET"


def confeditor_loader():
    return ESP32SocketConfEditor()

class ESP32SocketConfEditor(weewx.drivers.AbstractConfEditor):
    @property
    def default_stanza(self):
        return """
[ESP32Socket]
    # This section is for the weewx ESP32 Socket driver

    # The websocket url to connect to
    host_url = ws://weather-socket.localdomain:5000/weather_stream 

    # The driver to use:
    driver = weewx.drivers.esp32_socket
"""


if __name__ == "__main__":
    station = ESP32Socket()
    for packet in station.genLoopPackets():
        print(weeutil.weeutil.timestamp_to_string(packet['dateTime']), packet)

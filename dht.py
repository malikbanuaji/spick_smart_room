#----------------dht.py-----------------------
#  file ini untuk membaca sensor DHT11
#  yang terintegrasi di raspberry pi

import Adafruit_DHT
import time
import traceback

class dhtmain():
    def __init__(self, p = 11, g = None):
        sensor_args = {'11': Adafruit_DHT.DHT11,'22': Adafruit_DHT.DHT22, '2302': Adafruit_DHT.AM2302 }
        if str(p) not in sensor_args and g is None:
            return 'error: DHT or GPIO is not defined'
        else:
            self.p = sensor_args[str(p)]
            self.g = g

    def readSensor(self, delay = 3.5):

        humidity, temperature = Adafruit_DHT.read(self.p, self.g)
        time.sleep(delay)
        if humidity is not None and temperature is not None:
            return {'status':'ok','temperature': int(temperature), 'humidity' : int(humidity)}
        else:
            return {'status':'error','temperature': '0', 'humidity' : '0'}

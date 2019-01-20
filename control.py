#  control.py
#  ---------------------------------
#  file ini merupakan pusat kontrol
#  seluruh sensor baik itu memanggil
#  atau menjalankan fungsi


import RPi.GPIO as GPIO

import time
import datetime
import dateutil.parser
import threading
import subprocess
import BH1750
import os
import dht
import traceback
import json

from gpiocontroler import cgpio

from configparser import ConfigParser


class controlCenter:
    def __init__(self):
        #used pin for stepper [4,17,27,22]
        self.DHT = dht.dhtmain(22,13)
        self.bh1750 = BH1750
        self.activePresentation = None
        self.PresentationActive = None
        self.presentationFolder = 'content/presentation'
        self.brightness = 0
        self.stop_auto_lamp = False
        self.stop_auto_brightness = False
        self.auto_brightness_threshold = 300
        self.auto_brightness_thread = None
        self.AutoLamp = autoLamp()
        self.cgpio = cgpio()


        self.all_config = {}


        with open('configuration.json', 'r') as fp:
            self.all_config = json.load(fp)

    def load(self):
        self.cgpio.load_all_gpio()

    def stopAutoBrightness(self):
        self.stop_auto_brightness = True

    def set_window_presentation(self, v):
        if v == 1:
            self.PresentationActive = True
        else:
            self.PresentationActive = False

    def startAutoBrightness(self):
        self.auto_brightness_thread = threading.Thread(target = self.autoBrightness, name = 'auto brightness')
        self.auto_brightness_thread.daemon = True
        self.auto_brightness_thread.start()

    def start_gpio_reader(self):
        t = threading.Thread(target = self.update, name = 'gpioreader')
        t.daemon = True
        t.start()

    def autoBrightness(self):
        self.brightness = 90
        change = False
        while True:
            try:
                if self.stop_auto_brightness:
                    time.sleep(6)
                    #print('disable', self.stop_auto_brightness)
                else:
                    lux = float(self.bh1750.readLight()['lux'])

                    if lux < 20:
                        change = False
                    else:
                        if lux < self.auto_brightness_threshold - 20:
                            self.brightness += 2
                        elif lux > self.auto_brightness_threshold + 20:
                            self.brightness -= 2
                        change = True

                    if self.brightness > 255:
                        self.brightness = 255
                        change = False
                        #print('brightness has reach maximum value')
                    elif self.brightness < 0:
                        self.brightness = 0
                        change = False
                        #print('brightness has reach maximum value')

                    if lux > self.auto_brightness_threshold - 20 and lux < self.auto_brightness_threshold + 20:
                        change = False

                    if change:
                        time.sleep(0.2)
                        #self.lamp(self.brightness)
                        self.cgpio.light_brightness(self.brightness)

                    else:
                        time.sleep(5)
            except:
                traceback.print_exc()
                pass
    #def get_presentation_state(self):
        #return self.Prese

    def update(self):
        pressed_exit = False
        try:
            while True:
                if self.PresentationActive == True:
                    g = self.cgpio.update()
                    if g:
                        if 'exit' in g:
                            pressed_exit = True

                        elif 'next' in g:
                            subprocess.call(['xdotool','search','--name','--onlyvisible','LibreOffice 5.2','key','Right',])
                            print('next')
                        elif 'previous' in g:
                            subprocess.call(['xdotool','search','--name','--onlyvisible','LibreOffice 5.2','key','Left',])
                            print('previous')

                    else:
                        pressed_exit = False
                        pressed_exit_time = datetime.datetime.now() + datetime.timedelta(seconds = 2)

                    if pressed_exit:
                        print('pressed')
                        if datetime.datetime.now() > pressed_exit_time :
                            self.closePresentation()

                    time.sleep(0.5)

                else:
                    time.sleep(5)
        except:
            traceback.print_exc()

    def checkPresentation(self):
        try:
            p = subprocess.check_output([
                'xdotool',
                'search',
                '--name',
                '--onlyvisible',
                'LibreOffice 5.2',
                'getwindowname'
            ])
        except subprocess.CalledProcessError:
            time.sleep(1)
            pass
        else:
            return p

    def curtain(self, state):
        self.cgpio.stepper(state)
            #self.stepperMain.motor(_state)
            #open the curtain by using stepper motor
            #close the curtain by using stepper motor

    def closePresentation(self):
        if self.activePresentation:
            #if s == 0:
            #    self.lamp(dc = 100.0)
                #self.stepperMain.motor('close')
            #elif s == 1:
            #    self.lamp(dc = 50.0)
            self.activePresentation.terminate()
            self.activePresentation = None
            self.set_window_presentation(0)
        #else:
            #if s == 1:
            #    self.lamp(dc = 50.0)

    def openPresentation(self, _lesson=None, _filename=None, googleFile = None):
        self.closePresentation()
        if googleFile:
            filepath = os.path.abspath(googleFile)
        elif _lesson and _filename:
            filepath = '{}.odp'.format(os.path.join(os.path.abspath(self.presentationFolder), _lesson, _filename))
        else:
            return 'please provide path for files'
        print(filepath)

        if not os.path.isfile('{}'.format(filepath)):
            print("file tidak ada")
            return "file tidak ada"

        try:
            self.activePresentation = subprocess.Popen([
                'libreoffice',
                '--show',
                '{}'.format(filepath),
                '--norestore',
                '--display',
                ':0'
            ])

        except:
            traceback.print_exc()

        else:
            t = 0
            window_name = ''
            while True:
                if t > 10:
                    break
                try:
                    window_name = self.checkPresentation()
                except:
                    time.sleep(1)
                    pass
                else:
                    try:
                        if window_name.decode('utf-8'):
                            if 'libreoffice 5.2' in window_name.decode('utf-8').lower():
                                print('found')
                                break
                    except:
                        pass
                        traceback.print_exc()
                t += 1
                print(window_name)
                time.sleep(1)

        finally:
            self.set_window_presentation(1)

    def printerPrint(self, file='', google_drive = False):
        path = os.path.join(os.path.abspath('content'), 'pdf_files', file) if not google_drive else os.path.abspath(file)

        if not file.lower().endswith('.pdf'):
            return 'Please send me a PDF file'
        else:
            subprocess.run([
                'lp',
                '-d',
                'EPSON_L220_Series',
                path
            ])
            #using subprocess to print using UNIX printer
            pass

    def ConfigAutoLamp(self, al = None):
        if not al:
            self.config = {
                'hidup' : [(datetime.datetime.now().replace(tzinfo = datetime.timezone(datetime.timedelta(hours = 7))) + datetime.timedelta(seconds = 5)).isoformat()],
                'mati' : [(datetime.datetime.now().replace(tzinfo = datetime.timezone(datetime.timedelta(hours = 7))) + datetime.timedelta(seconds = 10)).isoformat()]
                }
        else:
            self.config = al

        self.set_alarm_to = self.AutoLamp.refreshConfigTime(self.config)
        print(self.set_alarm_to)

    def startAutoLamp(self):
        t = threading.Thread(target = self.initAutoLamp)
        t.daemon = True
        t.start()

    def stopAutoLamp(self):
        self.stop_auto_lamp = True

    def jsonAutoLamp(self, startDateTime = None, endDateTime = None, dateTimeList = None, waktu = None, hm = None):
        if not hm:
            return 'on or off'

        if not startDateTime and not endDateTime and not dateTimeList:
            return 'please insert start date and end date'
        toJsonDays = []
        upWaktu = dateutil.parser.parse(waktu)
        if startDateTime or endDateTime:
            end_date_time = dateutil.parser.parse(endDateTime).replace(tzinfo = self.AutoLamp.utc7, hour = upWaktu.hour, minute = upWaktu.minute, second = upWaktu.second) + datetime.timedelta(days=-7)
            start_date_time = dateutil.parser.parse(startDateTime).replace(tzinfo = self.AutoLamp.utc7, hour = upWaktu.hour, minute = upWaktu.minute, second = upWaktu.second) + datetime.timedelta(days=-7)
            deltaDays =  end_date_time - start_date_time
            toJson = {}

            for i in range(deltaDays.days + 1):
                toJsonDays.append((start_date_time + datetime.timedelta(days=i)).isoformat())

        if dateTimeList:
            for j in dateTimeList:
                newD = dateutil.parser.parse(j).replace(tzinfo = self.AutoLamp.utc7, hour = upWaktu.hour, minute = upWaktu.minute, second = upWaktu.second)
                new_date = newD + datetime.timedelta(days=-7)
                toJsonDays.append(new_date.isoformat())
        return {hm : toJsonDays}

    def jsonConfigEdit(self, data):
        print(data)
        with open('configuration.json' , 'r+') as fp:
            _data = json.load(fp)
            for i in data:
                _data['auto_lamp']['alarm'][i] = data[i]
            _data['auto_lamp']['start'] = True
            fp.seek(0)
            json.dump(_data, fp, indent = 4)
            fp.truncate()
            fp.close()
            self.ConfigAutoLamp(_data['auto_lamp']['alarm'])

    def initAutoLamp(self):
        #print(self.setAlarmTo['hidup'], self.setAlarmTo['mati'])
        self.stop_auto_lamp = False
        while True:
            if self.stop_auto_lamp:
                break

            date_now = datetime.datetime.now().replace(tzinfo = self.AutoLamp.utc7)
            for alarmTo in self.set_alarm_to:
                if date_now > self.set_alarm_to[alarmTo]:
                    if alarmTo == 'hidup':
                        print('Lampu nyala')
                        self.cgpio.light_brightness(255)
                        time.sleep(1)
                        self.stop_auto_brightness = False
                    else:
                        print('lampu mati')
                        self.stop_auto_brightness = True
                        time.sleep(1)
                        self.cgpio.light_brightness(0)

                    self.set_alarm_to = self.AutoLamp.refreshConfigTime(self.config)


            time.sleep(5)

    def clean(self):
        self.cgpio.clear()
        print("cleaning all GPIO pin")

class autoLamp():
    def __init__(self):
        self.utc7 = datetime.timezone(datetime.timedelta(hours=7))

    def refreshConfigTime(self, _alarm = None):
        if not _alarm:
            return 'masukan waktu'

        self.alarmOnOff = {
            'hidup' : [None] * len(_alarm['hidup']),
            'mati' : [None] * len(_alarm['mati'])
            }
        self.alarmOnOffSeconds = {
            'hidup' : [None] * len(_alarm['hidup']),
            'mati' : [None] * len(_alarm['mati'])
            }
        self.setAlarmTo = {'hidup' : None, 'mati' : None}


        dateWeekday = datetime.datetime.now().replace(tzinfo = self.utc7).isoweekday()

        for a in _alarm:
            print(a)
            newAlarm = None
            for num, i in enumerate(_alarm[a]):
                dateAlarm = dateutil.parser.parse(i).replace(tzinfo = self.utc7)
                time.sleep(2)
                dateNow = datetime.datetime.now().replace(tzinfo = self.utc7)

                deltaSeconds = dateAlarm - dateNow

                d , t = divmod(deltaSeconds.total_seconds(), 86400)
                deltaDays = d % 7

                if datetime.time(dateAlarm.hour, dateAlarm.minute, dateAlarm.second) < datetime.time(dateNow.hour, dateNow.minute, dateNow.second):
                    deltaDays += 1

                updateDays = datetime.timedelta(days = deltaDays)

                newAlarm = dateNow.replace(hour = dateAlarm.hour,
                    minute = dateAlarm.minute,
                    second = dateAlarm.second,
                    microsecond = 0) + updateDays
                print(dateAlarm, newAlarm, t)

                newDeltaSeconds = newAlarm - dateNow
                self.alarmOnOff[a][num] = newAlarm
                self.alarmOnOffSeconds[a][num] = newDeltaSeconds.total_seconds()
            self.setAlarmTo[a] = self.alarmOnOff[a][self.alarmOnOffSeconds[a].index(min(self.alarmOnOffSeconds[a]))]

            #print(self.alarmOnOffSeconds[a])
            #print(min(self.alarmOnOffSeconds[a]))
        #self.setAlarmTo['mati'] = self.alarmMati[self.alarmMatiSecond.index(min(self.alarmMatiSecond))]

        return self.setAlarmTo

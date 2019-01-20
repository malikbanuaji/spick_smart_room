#--------------mainappv3.py---------------
#  file ini merupakan file utama untuk
#  menjalankan sistem

import pyrebase
import time
import threading
import traceback
import json
import pathlib

from werkzeug.utils import secure_filename
from flask import Flask, jsonify, request, make_response, render_template, Response
import os
from control import controlCenter

from googleTasker import googleDriveExport

app = Flask(__name__)
app.secret_key = b'\xc8\xa6\xbb\x8b\x8b}\x8a\x05\xaa\xa26\x0cm\xa6J1\xd440G\x19.Z\x86' #secret key dipakai untuk login

# path untuk setiap mata pelajaran yang ingin di upload
UPLOAD_FOLDER = os.path.join(os.path.abspath(''), 'content', 'presentation')
ALLOWED_EXTENSTION = ['.pdf','.odp','.ppt','.pptx']

#pengaturan awal
json_data_default = {
    'auto_lamp':{
        'alarm': {'hidup' : ["2019-01-18T19:20:00+07:00"], 'mati' : ["2019-01-18T19:20:00+07:00"]},
        'start' : 'false'},
    'tirai' : 0,
    'config' : {
        'apiKey': "",           # API key yang ada di firebase
        'authDomain': "",       # Seluruh config dapat dilihat
        'databaseURL': "",      # di firebase yang dibuat sebelumnya
        'storageBucket': ""     #
    },
    'user' : {
        'username' : '',        #username merupakan gmail yang sudah didaftarkan di firebase
        'password' : ''         #password dari username yang bersangkutan
    }
}

p = pathlib.Path('configuration.json').is_file()
if not p:
    with open('configuration.json','w') as fpo:
        json.dump(json_data_default, fpo, indent = 4)
        fpo.close()

with open('configuration.json','r') as fp:
    data = json.load(fp)



#daftar pelajaran
lessons = [
	'matematika',
    'bahasa indonesia',
    'bahasa inggris',
    'geografi',
    'bahasa mandarin',
    'agama',
]
#maksimal sesi yang ada dalam 1 semester
max_sessions = 20

try:
    if not os.path.exists(os.path.join(os.path.abspath(''),'content')):
        os.mkdir(os.path.join(os.path.abspath(''),'content'))
    if not os.path.exists(os.path.join(os.path.abspath('content'),'presentation')):
        os.mkdir(os.path.join(os.path.abspath('content'),'presentation'))
    if not os.path.exists(os.path.join(os.path.abspath('content'),'pdf_files')):
        os.mkdir(os.path.join(os.path.abspath('content'),'pdf_files'))
except:
    print('pembuatan folder \"content\" gagal')

if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

for lesson in lessons:
    l = os.path.join(os.path.abspath(UPLOAD_FOLDER), lesson)
    if not os.path.exists(l):
        os.mkdir(l)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Deklarasi module
controlCenterApp = controlCenter()


'''
def s():
    while True:
        _dht = controlCenterApp.DHT.readSensor(1)	#Membaca sensor suhu dan kelembapan
        _l =  controlCenterApp.bh1750.readLight()	#membaca Intensitas cahaya di ruangan
        yield "data: {\"t\" : %s, \"h\" : %s, \"l\" : %s}\n\n" %(_dht['temperature'], _dht['humidity'], _l['lux'])
        #yield 'data: {}\n\n'.format(time.time())	#data yang dikirimkan dalam bentuk JSON
        time.sleep(5)
'''

class runForever(object):
    def run_as_thread(self, *args, **kwargs):
        t = threading.Thread(target = self.run_forever, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()

class SpickSensor(runForever):
    global controlCenterApp
    def __init__(self):
        self.all_sensor = {"temperature" : None, "humidity" : None, "light_intentsity" : None}

    def run_forever(self, delay = 2, web = False):
        print("lmao")
        while True:
            _dht = controlCenterApp.DHT.readSensor(1)
            _l =  controlCenterApp.bh1750.readLight()

            #if not web:
            try:
                if _dht['temperature'] or _dht['humidity'] or _l['lux']:

                    self.all_sensor = {"temperature" : _dht['temperature'], "humidity" : _dht['humidity']}
                    time.sleep(1)
                    self.all_sensor["light_intentsity"] = _l['lux']
                    #print(self.all_sensor)
            except:
                traceback.print_exc()
            #else:
                #yield "data: {\"temperature\" : %s, \"humidity\" : %s, \"light_intentsity\" : %s}\n\n" %(_dht['temperature'], _dht['humidity'], _l['lux'])
            #else:

            time.sleep(delay)
    def read_all(self):
        return self.all_sensor



class SpickLoop(runForever):
    global controlCenterApp
    def __init__(self, config):

        self.config = config

        self.firebase = pyrebase.initialize_app(self.config)
        self.auth = self.firebase.auth()
        self.db = self.firebase.database()


        self.timeFirst = time.time()

    def log_in(self, username, password):
        self.user = self.auth.sign_in_with_email_and_password(username, password)
        #print(self.user)

    def run_forever(self):
        #self.ts()
        while True:
            if time.time() - self.timeFirst > 3500:
                try:
                    self.user = self.auth.refresh(self.user['refreshToken'])

                except:
                    traceback.print_exc()

                else:
                    print('Token has been refresh')
                    self.ts()
                    self.timeFirst = time.time()

            time.sleep(5)


    def ts(self):
        print(self.user['idToken'])

    def firebase_sensor(self):
        _spick_sensor = SpickSensor()
        _spick_sensor.run_as_thread()
        while True:
            #try:

            #print(_spick_sensor.read_all())
            time.sleep(2)
            self.db.child("sensor").update(_spick_sensor.read_all(), self.user['idToken'])
            #except:
                #traceback.print_exc()
    def firebase_sensor_run_as_thread(self):
        t = threading.Thread(target = self.firebase_sensor)
        t.daemon = True
        t.start()

    def stream_handler(self, message):
        try:
            _event = message["event"]
            _path = message["path"]
            _data = message["data"]
            #print(_event, _path, _data)

        except Exception as e:
            traceback.print_exc()

        else:
            try:
                if '/presentasi' in _path:
                    if not _data['done'] or _data['done'] == 0:
                        print("opening presentation")
                        try:
                            self.db.child("presentasi").update({'done': True, 'timestamp' : time.time()}, self.user['idToken'])
                        except:
                            traceback.print_exc()
                        else:
                            try:
                                controlCenterApp.openPresentation(_data['p'], _data['s'])
                            except:
                                traceback.print_exc()

                elif '/elektronik/pelajaran' in _path:
                    if not _data['done'] or _data['done'] == 0:
                        controlCenterApp.closePresentation()
                        try:
                            self.db.child("elektronik").child('pelajaran').update({'done': True, 'timestamp' : time.time()}, self.user['idToken'])
                        except:
                            traceback.print_exc()

                elif '/elektronik/lampu/manual' in _path:
                    if not _data['done'] or _data['done'] == 0:
                        print(_data)
                        try:
                            print('updating db')
                            self.db.child("elektronik").child('lampu').child('manual').update({'done': True, 'timestamp' : time.time()}, self.user['idToken'])
                        except:
                            traceback.print_exc()
                        else:
                            try:
                                print('changing brightness')
                                if _data['brightness'] > 0:
                                    controlCenterApp.stop_auto_brightness = False
                                    time.sleep(0.15)
                                    controlCenterApp.cgpio.light_brightness(_data['brightness'])
                                    print("turn on the lights")

                                else:
                                    controlCenterApp.stopAutoBrightness()
                                    time.sleep(0.15)
                                    controlCenterApp.cgpio.light_brightness(0)
                                    print("turn off the lights")

                            except:
                                traceback.print_exc()

                elif '/elektronik/tirai' in _path:
                    if not _data['done'] or _data['done'] == 0:
                        print("tirai")
                        try:
                            controlCenterApp.cgpio.stepper(_data['tirai'])
                            self.db.child("elektronik").child('tirai').update({'done': True, 'timestamp' : time.time()}, self.user['idToken'])
                        except:
                            traceback.print_exc()

                elif _path == '/elektronik/pengaturanlampu/mati':
                    if not _data['done'] or _data['done'] == 0:
                        jsondata = {'startDateTime' : None, 'endDateTime' : None}
                        datelist = []
                        jsondata['jam'] = _data['jam']
                        print(_data['waktu'])
                        try:
                            for i in _data['waktu']:
                                if 'date_period' in i:
                                    jsondata['startDate'] = i['date_period']['startDate']
                                    jsondata['endDate'] = i['date_period']['endDate']
                                if 'recent' in i['date']:
                                    datelist.append(i['date']['recent'])
                                else:
                                    datelist.append(i['date'])

                            print('ini data', jsondata)
                        except:
                            traceback.print_exc()
                            pass
                        else:
                            d = controlCenterApp.jsonAutoLamp(startDateTime = jsondata['startDateTime'], endDateTime = jsondata['endDateTime'], dateTimeList = datelist, waktu = jsondata['jam'], hm = 'mati')
                            controlCenterApp.jsonConfigEdit(d)
                            self.db.child("elektronik").child("pengaturanlampu").child("mati").update({'done': True, 'timestamp' : time.time()}, self.user['idToken'])

                elif _path == '/elektronik/pengaturanlampu/nyala':
                    if not _data['done'] or _data['done'] == 0:
                        jsondata = {'startDateTime' : None, 'endDateTime' : None}
                        datelist = []
                        jsondata['jam'] = _data['jam']
                        print(_data['waktu'])
                        try:
                            for i in _data['waktu']:
                                if 'date_period' in i:
                                    jsondata['startDate'] = i['date_period']['startDate']
                                    jsondata['endDate'] = i['date_period']['endDate']
                                if 'recent' in i['date']:
                                    datelist.append(i['date']['recent'])
                                else:
                                    datelist.append(i['date'])

                            print('ini data', jsondata)
                        except:
                            traceback.print_exc()
                            pass
                        else:
                            d = controlCenterApp.jsonAutoLamp(startDateTime = jsondata['startDateTime'], endDateTime = jsondata['endDateTime'], dateTimeList = datelist, waktu = jsondata['jam'], hm = 'hidup')
                            controlCenterApp.jsonConfigEdit(d)
                            self.db.child("elektronik").child("pengaturanlampu").child("nyala").update({'done': True, 'timestamp' : time.time()}, self.user['idToken'])

                elif _path == '/gprint':
                    if not _data['done'] or _data['done'] == 0:

                        filepath = googleDriveExport(_data['linkid'], 'document')
                        try:
                            controlCenterApp.printerPrint(filepath, google_drive = True)
                        except:
                            traceback.print_exc()
                        else:
                            self.db.child("gprint").update({'done': True, 'timestamp' : time.time()}, self.user['idToken'])
                elif _path == '/gpresentasi':
                    if not _data['done'] or _data['done'] == 0:

                        filepath = googleDriveExport(_data['linkid'], 'presentation')
                        try:
                            controlCenterApp.openPresentation(googleFile = filepath)
                        except:
                            traceback.print_exc()
                        else:
                            self.db.child("gpresentasi").update({'done': True, 'timestamp' : time.time()}, self.user['idToken'])
            except:
                traceback.print_exc()
                print(_data)
                pass

        finally:
            time.sleep(1)

    def stream_handler_begin(self):
        self.presentasi_stream = self.db.stream(self.stream_handler, stream_id = "new_presentasi")
    def stream_handler_stop(self):
        self.presentasi_stream.close()






@app.route('/allsensor', methods=['GET'])
def dhtsensor():

    def s():
        while True:
            sensor = spick.db.child('sensor').get()
            yield "data: {\"t\" : %s, \"h\" : %s, \"l\" : %s}\n\n" %(sensor.val()['temperature'], sensor.val()['humidity'], sensor.val()['light_intentsity'])
            time.sleep(2)
    return Response(s(), mimetype='text/event-stream')

# Domain untuk menu utama
@app.route('/', methods=['GET'])
def home():
    a = spick.db.child('sensor').get()
    print(a.val())
    return render_template('index.html', lesson = lessons, session = max_sessions,)


@app.route('/printer', methods=['GET','POST'])
def printer():
    if request.method == 'GET':
        return render_template('print.html')
    if request.method == 'POST':
        file = request.files['file']

        filename = secure_filename(file.filename)
        name, extension = os.path.splitext(filename.lower())
        if '.pdf' not in extension.lower() :
            return jsonify(status = 'error', msg ='File harus dalam bentuk pdf')

        file.save(os.path.join(os.path.abspath('content'), 'pdf_files', filename))
        try:
            controlCenterApp.printerPrint(file = filename)
        except:
            traceback.print_exc()
            return jsonify(status = 'error', msg ='terjadi kesalahan')
        else:
            return jsonify(status = 'ok', msg = 'berhasil')

# proses pengunggahan berkas
@app.route('/lesson', methods=['POST'])
def upload(p=''):
    if request.method == 'POST':
        print(request.files)
        if 'file' not in request.files:
            return jsonify(status = 'error', msg = "File yang diunggah tidak ada")

        file = request.files['file']
        if file.filename == '':
            return jsonify(status = 'error', msg = "tidak ada file yang diunggah")

        json = request.form
        lesson = json.get('lesson')
        session = json.get('session')

        print(lesson, session)

        filename = secure_filename(file.filename)
        name, extension = os.path.splitext(filename.lower())
        if extension.lower() not in ALLOWED_EXTENSTION:
            return jsonify(status = 'ok', msg = 'Ekstensi file tidak cocok')


        file.save(os.path.join(app.config['UPLOAD_FOLDER'], lesson.lower(), filename))
        os.rename(os.path.join(app.config['UPLOAD_FOLDER'], lesson.lower(), filename), os.path.join(app.config['UPLOAD_FOLDER'], lesson.lower(), '{}{}'.format(session, extension)))

    return jsonify(status = 'ok', msg = "proses pengunggahan berhasil")





if __name__ == '__main__':

    spick = SpickLoop(data['config'])

    if data['user']['username'] == '' or not data['user']['username']:
        data['user']['username'] = input('registered username on firebase: ')
    if data['user']['password'] == '' or not data['user']['password']:
        data['user']['password'] = input('password: ')

    spick.log_in(data['user']['username'], data['user']['password'])

    with open('configuration.json','w') as fpo:
        json.dump(data, fpo, indent = 4)
        fpo.close()

    spick.firebase_sensor_run_as_thread()

    spick.run_as_thread()
    spick.stream_handler_begin()


    try:
        controlCenterApp.load()

    except:
        traceback.print_exc()
        controlCenterApp.clean()

    if data['auto_lamp']['start'] == True:
        controlCenterApp.ConfigAutoLamp(data['auto_lamp']['alarm'])
        controlCenterApp.startAutoLamp()

    controlCenterApp.startAutoBrightness()
    controlCenterApp.start_gpio_reader()



    print("Begin all thread")



    try:
        app.run('0.0.0.0', port = 5000, threaded=True)
        while 1:
            time.sleep(600)
    except KeyboardInterrupt:
        controlCenterApp.cgpio.clear()
        spick.stream_handler_stop()

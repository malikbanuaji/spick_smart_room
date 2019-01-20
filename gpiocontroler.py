import pigpio
import time
import traceback
import json
import atexit

class cgpio:
    def __init__(self):
        self.pwm_pin = 12
        self.stepper_pin = [4,17,27,22]
        self.slide_button = {'next' : 5, 'previous' : 6, 'exit' : 26}
        self.pi = pigpio.pi()

        self.waitTime = 1
        self.delay = int(self.waitTime)/float(1000)
        self.pattern_stepper = [
            [1,0,0,1],
            [1,0,0,0],
            [1,1,0,0],
            [0,1,0,0],
            [0,1,1,0],
            [0,0,1,0],
            [0,0,1,1],
            [0,0,0,1],
        ]
        self.stepCount = len(self.pattern_stepper)

    def light_brightness(self, v):
        #print(v)
        self.pi.set_PWM_dutycycle(self.pwm_pin, v)

    def load_all_gpio(self):
        print('load all gpio')
        for pin in self.slide_button:
            print(pin)
            self.pi.set_pull_up_down(self.slide_button[pin], pigpio.PUD_DOWN)
        for s_pin in self.stepper_pin:
            self.pi.set_mode(self.slide_button[pin], pigpio.OUTPUT)

    def stepper(self, states):
        stepCounter = 0
        if states == None:
            return 'Error'

        data = {}
        with open('configuration.json','r') as fp:
            data = json.load(fp)
        print(data)
        if states == 1:
            if int(data['tirai']) != 0:      #cek jika konfigurasi tirai
                return 'not running {}'.format(states)
            stepDir = 1

        elif states == 0:
            if int(data['tirai']) != 1:
                return 'not running {}'.format(states)
            stepDir = -1

        with open('configuration.json' , 'r+') as fp:
            data = json.load(fp)
            data['tirai'] = states
            fp.seek(0)
            json.dump(data, fp, indent = 4)
            fp.truncate()
            fp.close()

        for i in range(25000):
            try:
                for pin in range(0,4):
                    xpin = self.stepper_pin[pin]
                    if self.pattern_stepper[stepCounter][pin] != 0:
                        self.pi.write(xpin, 1)
                    else:
                        self.pi.write(xpin, 0)
                stepCounter += stepDir

                if (stepCounter >= self.stepCount):
                    stepCounter = 0
                if (stepCounter < 0):
                    stepCounter = self.stepCount + stepDir

                time.sleep(self.delay)
            except:
                traceback.print_exc()
                break


        for p in self.stepper_pin:
            self.pi.write(p, 0)

    def update(self):
        for p in self.slide_button:
            value = self.pi.read(self.slide_button[p])
            if value > 0:
                return p
        return False

    def clear(self):
        self.pi.set_PWM_dutycycle(self.pwm_pin, 0)
        self.pi.set_mode(self.pwm_pin, pigpio.INPUT)
        for pin in self.slide_button:
            self.pi.write(self.slide_button[pin], 0)
            self.pi.set_mode(self.slide_button[pin], pigpio.INPUT)
        for s_pin in self.stepper_pin:
            self.pi.write(s_pin, 0)
            self.pi.set_mode(s_pin, pigpio.INPUT)

        self.pi.stop()

from RPi import GPIO
import time
from .constants import morse_code

class Buzzer(object):
    def __init__(self, pin):
        GPIO.setmode(GPIO.BOARD)
        self.pin = pin
        GPIO.setup(pin, GPIO.OUT)

    def beep(self, beeptime):
        GPIO.output(self.pin, 1)
        time.sleep(beeptime)
        GPIO.output(self.pin, 0)

    def beep_beep(self, beeptime, sleeptime, duration):
        cycle = beeptime + sleeptime
        if cycle > duration:
            reps = range(1)
        else:
            reps = range(int(duration/cycle))
        for r in reps:
            self.beep(beeptime)
            time.sleep(sleeptime)

    @staticmethod
    def close():
        GPIO.cleanup()


class Morse(Buzzer):
    def dot(self):
        print(".")
        self.beep(0.1)
        time.sleep(0.05)

    def dash(self):
        print("-")
        self.beep(0.3)
        time.sleep(0.05)

    def __letter(self, l):
        try:
            pattern = morse_code[l]
        except:
            time.sleep(0.1)
            return
        for c in pattern:
            if c == ".":
                self.dot()
            elif c == "-":
                self.dash()

    def message(self, msg):
        msg.split(" ")
        for part in msg:
            for letter in part:
                self.__letter(letter)
            time.sleep(0.3)

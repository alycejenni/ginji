import argparse
import RPi.GPIO as GPIO
import time
import os

GPIO.setmode(GPIO.BOARD)
GPIO.setup(12, GPIO.OUT)
p = GPIO.PWM(12, 50)

state_file = 'lock_state'


def turn(servo, lock=True):
    n = 3 if lock else 7.5
    servo.start(n)
    servo.ChangeDutyCycle(n)
    print("locked" if lock else "opened")
    time.sleep(1)
    with open(state_file, "w") as file:
        file.write(str(int(lock)))


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('mode', metavar='N', type=str, help='open, close, or toggle')
    arg_parser.add_argument('-d', '--delay', type=int, default=0,
                            help='for delayed execution; number of seconds before executing the action')
    args = vars(arg_parser.parse_args())
    print(args)
    try:
        mode = args['mode']
        time.sleep(args['delay'])
        if mode == 'open':
            turn(p, False)
        elif mode == 'close':
            turn(p)
        elif mode == 'toggle':
            if os.path.exists(state_file):
                with open(state_file, 'r') as file:
                    c = file.read()
                turn(p, c == '0')
            else:
                turn(p)
    except IndexError:
        turn(p)

p.stop()
GPIO.cleanup()

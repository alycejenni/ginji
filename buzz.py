import buzzer
import argparse


class Beep(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        setattr(namespace, self.dest, values)
        beeper = buzzer.Buzzer(buzzer.buzzer_pin)
        b = float(values[0])
        s = 0
        if len(values) > 1:
            s = float(values[1])
        else:
            beeper.beep(b)
        if len(values) > 2:
            d = float(values[2])
        else:
            d = 0
        beeper.beep_beep(b, s, d)
        beeper.close()


class MorseCode(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        setattr(namespace, self.dest, values)
        beeper = buzzer.Morse(buzzer.buzzer_pin)
        msg = " ".join(values)
        beeper.message(msg)
        beeper.close()


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-b", "--beep", required = False,
                            help = "beeptime, sleeptime, duration", nargs = '+', action = Beep)
    arg_parser.add_argument("-m", "--message", required = False,
                            help = "message to translate into morse code", nargs='*', action = MorseCode)
    args = vars(arg_parser.parse_args())

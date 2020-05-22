from models import *

# NOTIFIER
notifier = Notifier(".config/catflap_open.json")

# OUTPUTS
txt = TextOutput(0, notifier)

# OBSERVERS
open_observer = Observer(txt.fire)

# INPUTS
open_pin = InputWithFreeze(40, {
    0: 5
}, printable={
    0: "OPEN",
    1: "CLOSED"
}, hold=0.1)
open_pin.add_observer(open_observer)

# THE PROGRAM
open_pin.start()
while True:
    try:
        time.sleep(60)
    except KeyboardInterrupt:
        print("Quitting...")
        open_pin.stop()
        break
    except Exception as e:
        print(e)
        open_pin.reset()

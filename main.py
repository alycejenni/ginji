from logger import logger
from models import *
from outputs import *
from inputs import *
import argparse
import sys
import os


PREFIX = os.path.dirname(os.path.realpath(__file__)) + '/'

# MANUAL INPUTS
ldr = InputCapacitorDischarge(13, 3000)
pot = InputCapacitorDischarge(11, 3000)
mic = InputMicrophone()

# INPUTS
open_pin = InputWithFreeze(40, {
    0: 5
}, printable={
    0: "OPEN",
    1: "CLOSED"
}, hold=0.1)
direction_pin = InputWithFreeze(37, {
    1: 10
}, printable={
    0: "NOT TRIGGERED",
    1: "OPENED INWARDS"
})


def stills():
    logger.debug("starting switch-based stills capture")
    # UPLOADER
    uploader = Uploader(PREFIX + ".config/catflap_open.json")
    # OUTPUTS
    camera = CameraOutput(0, uploader=(uploader, PREFIX + ".config/services_1.json"))
    camera.add_manual_input(ldr, "ldr")
    camera.add_manual_input(pot, "backup")
    # OBSERVERS
    open_observer = Observer(camera.fire)
    direction_observer = Observer(camera.file_handler.set_direction)
    open_pin.add_observer(open_observer)
    direction_pin.add_observer(direction_observer)
    return camera


def video():
    logger.debug("starting switch-based video capture")
    # UPLOADER
    uploader = Uploader(PREFIX + ".config/catflap_open_video.json")
    # OUTPUTS
    videocam = VideoCameraOutput(0, uploader=(uploader, PREFIX + ".config/services_1.json"))
    videocam.add_manual_input(pot, "backup")
    videocam.add_manual_input(ldr, "ldr")
    videocam.add_manual_input(mic, "mic")
    # OBSERVERS
    open_observer = Observer(videocam.fire)
    direction_observer = Observer(videocam.file_handler.set_direction)
    open_pin.add_observer(open_observer)
    direction_pin.add_observer(direction_observer)
    return videocam


def motion():
    logger.debug("starting motion detection")
    # UPLOADER
    uploader = Uploader(PREFIX + ".config/catflap_open_video.json")
    motdet = MotionDetector(5, 5000, 20, uploader=(uploader, PREFIX + ".config/services_1.json"))
    if motdet.file_handler.pending:
        motdet.file_handler.run()
    motdet.start()
    while True:
        try:
            time.sleep(60)
        except KeyboardInterrupt:
            logger.debug("quitting nicely")
            motdet.save_bg()
            logger.debug("saved background")
            motdet.stop()
            motdet.file_handler.clean()
            logger.debug("bye!")
            break


def runcam(cam):
    # THE PROGRAM
    open_pin.start()
    direction_pin.start()
    while True:
        try:
            time.sleep(60)
        except KeyboardInterrupt:
            logger.debug("Quitting...")
            open_pin.stop()
            direction_pin.stop()
            cam.close()
            cam.file_handler.clean()
            break
        except Exception as e:
            logger.debug(e)
            open_pin.reset()
            direction_pin.reset()
            cam.file_handler.clean()


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-c", "--capture", required=True,
                            help="capture type e.g. video or stills")
    arg_parser.add_argument('--tidy', action='store_true',
                            help='tidy up any files that were not uploaded')
    args = vars(arg_parser.parse_args())
    if args['tidy']:
        untidy_files = [f for f in os.listdir(PREFIX) if f.endswith('.mp4')]
        uploader = Uploader(PREFIX + ".config/catflap_open_video.json")
        file_handler = FileHandler(filetype="h264", uploader=(uploader, PREFIX + ".config/services_1.json"))
        print(len(untidy_files))
        for f in untidy_files:
            file_handler.path = os.path.join(PREFIX, f)
            file_handler.upload()
            file_handler.clean()
    try:
        if args["capture"] == "video":
            runcam(video())
        elif args["capture"] == "manual":
            video().fire(0)
        elif args["capture"] == "stills":
            runcam(stills())
        elif args["capture"] == "motion":
            motion()
    except IndexError:
        stills()

from logger import logger
import subprocess
from datetime import datetime as dt

import cv2
from picamera.array import PiRGBArray
from scipy.io import wavfile
import numpy as np
import pickle
import os

from models import *


PREFIX = os.path.dirname(os.path.realpath(__file__)) + '/'

class PinInput(Input):
    def __init__(self, pin):
        self.pin = pin
        self.setup()

    def setup(self):
        GPIO.setup(self.pin, GPIO.IN)

    def get(self):
        return GPIO.input(self.pin)


class ContinuousInput(PinInput):
    def __init__(self, pin, interval = None, printable = None, hold = None):
        super(ContinuousInput, self).__init__(pin)
        self.interval = interval
        self.printable = printable
        self.hold = hold
        self.cont = True
        self.prev = 2
        self.cur = 0
        self.reset()
        self.thread = threading.Thread(target = self.checktrigger)
        self.observers = []

    def add_observer(self, observer):
        if isinstance(observer, Observer):
            self.observers.append(observer)

    def reset(self):
        self.setup()
        self.cont = True
        self.prev = 2
        self.cur = 0

    def checktrigger(self):
        while self.cont:
            self.cur = self.get()
            if self.cur != self.prev:
                if self.hold:
                    time.sleep(self.hold)
                    if self.cur == self.prev:
                        if self.interval:
                            time.sleep(self.interval)
                        continue
                self.prev = self.cur
                self.change(self.cur)
            if self.interval:
                time.sleep(self.interval)

    def change(self, value):
        if self.printable:
            logger.debug(self.printable[value])
        else:
            logger.debug(value)
        for o in self.observers:
            o.notify(value)

    def start(self):
        if not self.thread.is_alive():
            self.thread.start()

    def stop(self):
        self.cont = False
        self.thread.join()


class InputWithFreeze(ContinuousInput):
    def __init__(self, pin, freeze_values, interval = None, printable = None, hold = None):
        super(InputWithFreeze, self).__init__(pin, interval = interval, printable = printable)
        self.freeze_values = freeze_values
        # freeze values should be a dictionary of input value: freeze period

    def checktrigger(self):
        while self.cont:
            self.cur = self.get()
            if self.cur != self.prev:
                if self.hold:
                    time.sleep(self.hold)
                    if self.cur == self.prev:
                        if self.interval:
                            time.sleep(self.interval)
                        continue
                self.prev = self.cur
                self.change(self.cur)
                if self.cur in self.freeze_values.keys():
                    self.frozen = True
                    time.sleep(self.freeze_values[self.cur])
                    self.frozen = False
            if self.interval:
                time.sleep(self.interval)

    def wait_for_ready(self):
        if self.cur not in self.freeze_values.keys():
            return True
        elif self.frozen:
            return True
        else:
            self.checktrigger()
            self.wait_for_ready()


class InputCapacitorDischarge(PinInput):
    def __init__(self, pin, max_count):
        super(InputCapacitorDischarge, self).__init__(pin)
        self.max_count = max_count

    @property
    def get(self):
        count = 0
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        time.sleep(0.1)

        GPIO.setup(self.pin, GPIO.IN)

        # want to know the reason for loop termination
        pin_low = (GPIO.input(self.pin) == GPIO.LOW)
        while pin_low and count < self.max_count:
            count += 1
            pin_low = (GPIO.input(self.pin) == GPIO.LOW)
        self.count_exceeded = pin_low

        return count


class InputMicrophone(Input):
    def __init__(self):
        self.thread = threading.Thread(target = self.record)

    def record(self):
        audioname = "audio1.wav"
        p = subprocess.Popen(["arecord", "-D", "plughw:CARD=1", "-f", "S16_LE", "-q", "-d", "5", audioname])
        p.wait()
        freq, aud = wavfile.read(audioname)
        aud = abs(aud / (2. ** 15))
        os.remove(audioname)
        self.max_amp = max(aud)

    def get(self):
        self.thread.start()
        self.thread.join()
        self.thread = threading.Thread(target = self.record)


class MotionDetector(Input):
    def __init__(self, min_frames, min_area, max_silent_frames, uploader = None):
        self.cam = picamera.PiCamera()
        self.background = None
        self.bgfile = None
        self.last_update = dt.now()
        self.min_moving_frames = min_frames
        self.min_area = min_area
        self.max_silent_frames = max_silent_frames
        self.moving_frames = 0
        self.silent_frames = 0
        self.cont = True
        self.fps = 30
        self.thread = threading.Thread(target = self.checktrigger)
        self.file_handler = FileHandler(filetype = "mp4", uploader = uploader)
        self.setup()

    def setup(self):
        if not os.path.exists(PREFIX + "backgrounds"):
            os.mkdir(PREFIX + "backgrounds")
            self.bgfile = PREFIX + "backgrounds/bg1.pkl"
        else:
            bgfiles = os.listdir(PREFIX + "backgrounds")
            bgfiles = sorted(bgfiles, key = lambda x: os.path.getmtime(PREFIX + "backgrounds/" + x))

            # load the most recent bg file
            with open(PREFIX + "backgrounds/" + bgfiles[-1], "rb") as file:
                self.background = pickle.load(file)
            logger.debug("loaded background from " + bgfiles[-1])

            # now make a new file
            ix = int(bgfiles[-1].split(".")[0].replace("bg", "")) + 1
            fn = PREFIX + f"backgrounds/bg{ix}.pkl"
            while os.path.exists(fn):
                ix += 1
                fn = PREFIX + f"backgrounds/bg{ix}.pkl"
            self.bgfile = fn
            self.save_bg()

        self.cam.resolution = (640, 480)
        time.sleep(2)

    def save_bg(self):
        with open(self.bgfile, "wb") as file:
            pickle.dump(self.background, file)

    def start(self):
        self.cont = True
        if not self.thread.is_alive():
            self.thread.start()

    def stop(self):
        self.cont = False
        self.thread.join()

    def checktrigger(self):
        crop_top = 0.3
        crop_bottom = 0.9
        crop_right = 0.8
        raw_frame = PiRGBArray(self.cam, size = self.cam.resolution)
        vid_frames = []
        avg_centroids = []
        total_frames = 0
        total_time = 0
        for f in self.cam.capture_continuous(raw_frame, format = "bgr", use_video_port = True):
            start = dt.now()
            if not self.cont:
                break
            frame = f.array[int(480 * crop_top):int(480 * crop_bottom), 0:int(640 * crop_right)]
            imgrey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            imgrey = cv2.GaussianBlur(imgrey, (21, 21), 0)
            if self.background is None:
                self.background = imgrey.copy().astype("float")
                self.save_bg()
                raw_frame.truncate(0)
                logger.debug("initialised background")
                continue

            cv2.accumulateWeighted(imgrey, self.background, 0.5)
            frame_delta = cv2.absdiff(imgrey, cv2.convertScaleAbs(self.background))
            frame_threshold = cv2.threshold(frame_delta, 20, 255, cv2.THRESH_BINARY)[1]
            frame_dilated = cv2.dilate(frame_threshold, None, iterations = 10)
            im2, contours, hier = cv2.findContours(frame_dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            motion = [c for c in contours if cv2.contourArea(c) >= self.min_area]
            frame_centroids = []

            for c in motion:
                # x, y, w, h = cv2.boundingRect(c)
                # cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                m = cv2.moments(c)
                cx = int(m['m10'] / m['m00'])
                frame_centroids.append(cx)

            if len(motion) == 0:
                if self.moving_frames != 0:
                    self.silent_frames += 1
                    if self.silent_frames == self.max_silent_frames:
                        if self.moving_frames >= self.min_moving_frames:
                            logger.debug("movement ended")
                            try:
                                self.make_vid(vid_frames, avg_centroids)
                            except Exception as e:
                                logger.debug("failed to upload video")
                                logger.debug(e)
                        else:
                            logger.debug("false alarm, sorry")
                        self.save_bg()
                        self.moving_frames = 0
                        vid_frames.clear()
                        avg_centroids.clear()
                    else:
                        vid_frames.append(f.array)
                        avg_centroids.append(avg_centroids[-1])
            else:
                self.moving_frames += 1
                self.silent_frames = 0
                vid_frames.append(f.array)
                avg_centroids.append(np.mean(frame_centroids))
                if self.moving_frames == 1:
                    logger.debug("what was that??")
                if self.moving_frames == self.min_moving_frames:
                    logger.debug("movement detected")

            raw_frame.truncate(0)
            total_time += (dt.now() - start).microseconds / 1000000
            total_frames += 1
            self.fps = total_frames / total_time
            frame_centroids.clear()
        self.cam.close()
        logger.debug("camera closed, thread terminated")

    def make_vid(self, frames, centroids):
        direction = 1 if centroids[0] > centroids[-1] else 0
        if centroids[0] == centroids[-1]:
            direction = 2
        self.file_handler.set_direction(direction)
        fourcc = cv2.VideoWriter_fourcc(*'X264')
        out = cv2.VideoWriter(self.file_handler.initial, fourcc, np.floor(self.fps * 0.6), self.cam.resolution, True)
        for f in frames:
            out.write(f)
        out.release()
        logger.debug("renaming...")
        self.file_handler.standard()
        self.file_handler.rename()
        self.file_handler.upload()
        self.file_handler.clean()

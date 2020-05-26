import os
import pickle
import time
from datetime import datetime as dt
import numpy as np
import math
import cv2
import picamera
from picamera.array import PiRGBArray

from ginji.config import config, logger
from ._base import BaseInput


class MotionInput(BaseInput):
    config_name = 'motion'

    def __init__(self):
        self.cam = picamera.PiCamera()
        self.background = None
        self.bgfile = None
        self.cont = True
        self._motion = False
        super(MotionInput, self).__init__()

    def load_config(self):
        basic_config = super(MotionInput, self).load_config()
        return {
            'height': basic_config.get('height', 480),
            'width': basic_config.get('width', 640),
            'crop_top': basic_config.get('crop_top', 0),
            'crop_bottom': 1 - basic_config.get('crop_bottom', 0),
            'crop_left': basic_config.get('crop_left', 0),
            'crop_right': 1 - basic_config.get('crop_right', 0),
            'min_moving_frames': basic_config.get('min_moving_frames', 5),
            'min_area': basic_config.get('min_area', 5000),
            'max_silent_frames': basic_config.get('max_silent_frames', 20)
            }

    def setup(self):
        bg_path = os.path.join(config.root, 'backgrounds')
        if not os.path.exists(bg_path):
            os.mkdir(bg_path)
            self.bgfile = os.path.join(bg_path, 'bg1.pkl')
        else:
            bgfiles = os.listdir(bg_path)
            bgfiles = sorted(bgfiles, key=lambda x: os.path.getmtime(os.path.join(bg_path, x)))

            # load the most recent bg file
            with open(os.path.join(bg_path, bgfiles[-1]), 'rb') as file:
                self.background = pickle.load(file)
            logger.debug('loaded background from ' + bgfiles[-1])

            # now make a new file
            ix = int(bgfiles[-1].split('.')[0].replace('bg', '')) + 1
            fn = os.path.join(bg_path, f'bg{ix}.pkl')
            while os.path.exists(fn):
                ix += 1
                fn = os.path.join(bg_path, f'bg{ix}.pkl')
            self.bgfile = fn
            self.save_bg()

        self.cam.resolution = (self._config['width'], self._config['height'])
        time.sleep(2)

    def run(self):
        raw_frame = PiRGBArray(self.cam, size=self.cam.resolution)
        vid_frames = []
        avg_centroids = []
        moving_frames = 0
        silent_frames = 0
        total_frames = 0
        total_time = 0
        fps = 0
        for f in self.cam.capture_continuous(raw_frame, format='bgr', use_video_port=True):
            start = dt.now()
            if not self.cont:
                break
            frame = f.array[
                    int(480 * self._config['crop_top']):int(480 * self._config['crop_bottom']),
                    int(640 * self._config['crop_left']):int(640 * self._config['crop_right'])]
            imgrey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            imgrey = cv2.GaussianBlur(imgrey, (21, 21), 0)
            if self.background is None:
                self.background = imgrey.copy().astype('float')
                self.save_bg()
                raw_frame.truncate(0)
                logger.debug('initialised background')
                continue

            cv2.accumulateWeighted(imgrey, self.background, 0.5)
            frame_delta = cv2.absdiff(imgrey, cv2.convertScaleAbs(self.background))
            frame_threshold = cv2.threshold(frame_delta, 20, 255, cv2.THRESH_BINARY)[1]
            frame_dilated = cv2.dilate(frame_threshold, None, iterations=10)
            contours, hier = cv2.findContours(frame_dilated, cv2.RETR_TREE,
                                                   cv2.CHAIN_APPROX_SIMPLE)

            motion = [c for c in contours if cv2.contourArea(c) >= self._config['min_area']]
            frame_centroids = []

            for c in motion:
                m = cv2.moments(c)
                cx = int(m['m10'] / m['m00'])
                frame_centroids.append(cx)

            if len(motion) == 0:
                if moving_frames != 0:
                    silent_frames += 1
                    if silent_frames == self._config['max_silent_frames']:
                        self._motion = False
                        if moving_frames >= self._config['min_moving_frames']:
                            logger.debug('movement ended')
                            try:
                                self.output(vid_frames, math.floor(fps * 0.6), centroids=avg_centroids)
                            except Exception as e:
                                logger.debug('failed to upload video')
                                logger.debug(e)
                        else:
                            logger.debug('false alarm, sorry')
                        self.save_bg()
                        moving_frames = 0
                        vid_frames.clear()
                        avg_centroids.clear()
                    else:
                        vid_frames.append(f.array)
                        avg_centroids.append(avg_centroids[-1])
            else:
                moving_frames += 1
                silent_frames = 0
                vid_frames.append(f.array)
                avg_centroids.append(np.mean(frame_centroids))
                if moving_frames == 1:
                    logger.debug('what was that??')
                if moving_frames == self._config['min_moving_frames']:
                    self._motion = True
                    logger.debug('movement detected')

            raw_frame.truncate(0)
            total_time += (dt.now() - start).total_seconds()
            total_frames += 1
            fps = total_frames / total_time
            frame_centroids.clear()
        self.cam.close()
        logger.debug('camera closed, thread terminated')

    def save_bg(self):
        with open(self.bgfile, 'wb') as file:
            pickle.dump(self.background, file)

    @property
    def value(self):
        return self._motion

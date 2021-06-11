import os
import time

import cv2
import ffmpy

from ginji.config import config, logger
from ._base import BaseOutput


class MediaOutput(BaseOutput):
    def __init__(self, filetype='jpg'):
        super(MediaOutput, self).__init__()
        self.filetype = filetype
        self.file_root = os.path.join(config.root, 'media')
        if not os.path.exists(self.file_root):
            os.mkdir(self.file_root)
        self.initial = os.path.join(self.file_root, 'temp.' + filetype)
        self.path = os.path.join(self.file_root, 'temp.' + filetype)
        self.direction = 2
        self.filename_set = False
        self.time_taken = None
        self.processing = False

    @property
    def direction_msg(self):
        if self.direction == 1:
            return "came in"
        elif self.direction == 2:
            return "is being a quantum boy"
        else:
            return "went out"

    def set_direction(self, value):
        if not self.filename_set:
            self.direction = value

    def make_filename(self, time_object, direction):
        t = str(time_object).replace('.', '_')
        return os.path.join(self.file_root,
                            f'{config.file_prefix}_{t}-{direction}.' + self.filetype)

    def auto_filename(self):
        self.time_taken = time.time()
        self.path = self.make_filename(self.time_taken, self.direction)
        self.filename_set = True

    def rename(self):
        if os.path.exists(self.initial):
            os.rename(self.initial, self.path)
            logger.debug(f'renamed {self.initial} to {self.path}')

    def clean(self):
        """
        Clean up unnecessary files.
        :return:
        """
        if os.path.exists(self.initial):
            if os.path.exists(self.path) and os.stat(self.path).st_size == os.stat(
                    self.initial).st_size:
                os.remove(self.initial)
            else:
                # if it doesn't match, something probably crashed; rename the temporary file and
                # it'll get uploaded at some point
                self.auto_filename()
                self.rename()
                self.connect()
                os.remove(self.initial)
        if os.path.exists(self.path):
            os.remove(self.path)
        self.filename_set = False

    def tidy(self):
        untidy_files = [f for f in os.listdir(self.file_root) if f.endswith(self.filetype)]
        logger.debug(f'Tidying up {len(untidy_files)} leftover files.')
        for f in untidy_files:
            self.path = os.path.join(self.file_root, f)
            self.connect()
            self.clean()

    def fire(self, **kwargs):
        self.processing = True
        self.auto_filename()
        self.rename()
        if self.connect():
            logger.debug('Cleaning up.')
            self.clean()
        self.processing = False

    def connect(self, **kwargs):
        errors = 0
        uploads = {}
        for u in self._uploaders:
            try:
                uploads[u.config_name] = u.run(self.path)
            except Exception as e:
                logger.error(f'Unable to upload {self.path} to {u.config_name}.')
                errors += 1
        for n in self._notifiers:
            try:
                n.run(uploads, self.time_taken, self.direction_msg)
            except Exception as e:
                logger.error(f'Unable to send payload to {n.config_name}.')
                errors += 1
        return errors == 0


class VideoOutput(MediaOutput):
    def __init__(self, filetype='mp4'):
        super(VideoOutput, self).__init__(filetype)

    def fire(self, frames, fps, **kwargs):
        self.processing = True
        centroids = kwargs.get('centroids', None)
        if centroids is not None:
            direction = 1 if centroids[0] > centroids[-1] else 0
            if centroids[0] == centroids[-1]:
                direction = 2
            self.set_direction(direction)
        self.make_video(frames, fps)
        super(VideoOutput, self).fire()

    def make_video(self, frames, fps):
        fourcc = cv2.VideoWriter_fourcc(*'X264')
        shape = frames[0].shape[1::-1]
        out = cv2.VideoWriter(self.initial, fourcc, fps,
                              shape, True)
        for f in frames:
            out.write(f)
        out.release()

    def convert(self, newtype):
        ff = ffmpy.FFmpeg(inputs={
            self.path: None
            }, outputs={
            self.path.replace(self.filetype, newtype): None
            }, global_options=['-nostats -loglevel 0'])
        ff.run()
        self.clean()
        self.path = self.path.replace(self.filetype, newtype)

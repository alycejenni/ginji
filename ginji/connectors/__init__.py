from .s3_uploader import S3Uploader
from .drive_uploader import GoogleDriveUploader
from .ifttt_notifier import IFTTTNotifier


uploaders = [S3Uploader, GoogleDriveUploader]
notifiers = [IFTTTNotifier]

import os

import boto3

from ginji.config import logger
from ._base import BaseUploader


class S3Uploader(BaseUploader):
    config_name = 's3'

    def __init__(self):
        super(S3Uploader, self).__init__()
        self.client = boto3.client('s3',
                                   endpoint_url=self._config['host'])

    def load_config(self):
        basic_config = super(S3Uploader, self).load_config()
        return {
            'host': basic_config.get('host', 'invalid-url'),
            'bucket': basic_config.get('bucket', ''),
            'acl': basic_config.get('acl', 'public-read')
            }

    def run(self, file):
        _, filename = os.path.split(file)
        try:
            self.client.upload_file(file, self._config['bucket'], filename, ExtraArgs={
                'ACL': self._config['acl']
                })
        except Exception as e:
            logger.error(e)
        media_url = self.client.generate_presigned_url('get_object', Params={
            'Bucket': self._config['bucket'],
            'Key': filename
            }).split('?')[0]
        logger.debug(f'Uploaded {file} to S3 object store: {media_url}')
        return media_url

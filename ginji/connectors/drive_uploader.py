import argparse

import httplib2
import oauth2client
from apiclient import discovery
from oauth2client import client, tools

from ginji.config import logger
from ._base import BaseUploader


class GoogleDriveUploader(BaseUploader):
    config_name = 'google_drive'

    def __init__(self):
        super(GoogleDriveUploader, self).__init__()
        self.service = self.auth()

    def auth(self):
        store = oauth2client.file.Storage(self._config['credential_path'])
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self._config['client_secret'],
                                                  self._config['scopes'])
            flow.user_agent = self._config['app_name']
            credentials = tools.run_flow(flow, store, argparse.ArgumentParser(
                parents=[tools.argparser]).parse_args())
            logger.debug('Storing credentials to ' + self._config['credential_path'])
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('drive', 'v3', http=http)
        return service

    def run(self, file):
        metadata = {
            'name': file
            }
        self.service.files().create(body=metadata, media_body=file).execute()
        logger.debug(f'Uploaded {file} to Google Drive.')
        return ''

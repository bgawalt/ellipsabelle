from __future__ import print_function

import os
import sys
import time

import json
import requests
from requests_oauthlib import OAuth1


MEDIA_ENDPOINT_URL = 'https://upload.twitter.com/1.1/media/upload.json'
POST_TWEET_URL = 'https://api.twitter.com/1.1/statuses/update.json'


def GetConfig(filename):
    with open(filename, 'r') as infile:
        config = {}
        for line_id, line in enumerate(infile):
            spline = line.split(" = ")
            config[spline[0]] = spline[1].strip()
    return config


def GetOauth(config):
    ckey = config["CONSUMER_KEY"]
    csec = config["CONSUMER_SECRET"]
    akey = config["ACCESS_KEY"]
    asec = config["ACCESS_SECRET"]
    return OAuth1(ckey,
                  client_secret=csec,
                  resource_owner_key=akey,
                  resource_owner_secret=asec)


def GetFilename(posted_dir):
    valid_filenames = [f for f in sorted(os.listdir(posted_dir))
                       if f[0] != "." and f[-4:] == ".gif"]
    return valid_filenames[0]


class GifUploader(object):

    def __init__(self, file_name, oauth):
        self.video_filename = file_name
        self.oauth = oauth
        self.total_bytes = os.path.getsize(self.video_filename)
        self.media_id = None
        self.processing_info = None


    def upload_init(self):
        print('INIT')

        request_data = {
          'command': 'INIT',
          'media_type': 'image/gif',
          'total_bytes': self.total_bytes,
          'media_category': 'tweet_gif'
        }

        req = requests.post(url=MEDIA_ENDPOINT_URL, data=request_data,
                            auth=self.oauth)
        media_id = req.json()['media_id']

        self.media_id = media_id

        print('Media ID: %s' % str(media_id))


    def upload_append(self):
        segment_id = 0
        bytes_sent = 0
        file = open(self.video_filename, 'rb')

        while bytes_sent < self.total_bytes:
            chunk = file.read(4*1024*1024)

            print('APPEND')

            request_data = {
                'command': 'APPEND',
                'media_id': self.media_id,
                'segment_index': segment_id
                }

            files = {
                'media':chunk
            }

            req = requests.post(url=MEDIA_ENDPOINT_URL, data=request_data,
                                files=files, auth=self.oauth)

            if req.status_code < 200 or req.status_code > 299:
                print(req.status_code)
                print(req.text)
                sys.exit(0)

            segment_id = segment_id + 1
            bytes_sent = file.tell()

            print('%s of %s bytes uploaded' % (str(bytes_sent),
                  str(self.total_bytes)))

        print('Upload chunks complete.')


    def upload_finalize(self):
        print('FINALIZE')

        request_data = {
          'command': 'FINALIZE',
          'media_id': self.media_id
        }

        req = requests.post(url=MEDIA_ENDPOINT_URL, data=request_data,
                            auth=self.oauth)
        print(req.json())

        self.processing_info = req.json().get('processing_info', None)
        self.check_status()


    def check_status(self):
        if self.processing_info is None:
          return

        state = self.processing_info['state']

        print('Media processing status is %s ' % state)

        if state == u'succeeded':
          return

        if state == u'failed':
          sys.exit(0)

        check_after_secs = self.processing_info['check_after_secs']

        print('Checking after %s seconds' % str(check_after_secs))
        time.sleep(check_after_secs)

        print('STATUS')

        request_params = {
          'command': 'STATUS',
          'media_id': self.media_id
        }

        req = requests.get(url=MEDIA_ENDPOINT_URL, params=request_params,
                           auth=self.oauth)

        self.processing_info = req.json().get('processing_info', None)
        print(req.json())
        self.check_status()


    def tweet(self):
        request_data = {
          #'status': '',
          'media_ids': self.media_id
        }

        req = requests.post(url=POST_TWEET_URL, data=request_data,
                            auth=self.oauth)
        print(req.json())


if __name__ == '__main__':
    config = GetConfig(sys.argv[1])
    auth = GetOauth(config)
    gif_filename = GetFilename(config["SRC_FOLDER"])
    source = os.path.join(config["SRC_FOLDER"], gif_filename)
    print(gif_filename)

    gu = GifUploader(source, auth)
    gu.upload_init()
    gu.upload_append()
    gu.upload_finalize()
    gu.tweet()

    source = os.path.join(config["SRC_FOLDER"], gif_filename)
    destination = os.path.join(config["DST_FOLDER"], gif_filename)

    os.rename(source, destination)

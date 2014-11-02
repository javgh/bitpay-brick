#!/usr/bin/env python

import urllib
import requests

EVENT_URL = 'https://bitpay.com/events'
CONTENT_TYPE_HEADER = {'content-type': 'text/event-stream'}
SUBSCRIBE_QUERY = 'action=subscribe&events%%5B%%5D=payment&token=%s'

class BitPayEventSource:
    def __init__(self, token):
        self.token = token

    def start(self):
        params = SUBSCRIBE_QUERY % self.token
        r = requests.get(EVENT_URL, headers=CONTENT_TYPE_HEADER, params=params,
                stream=True)
        print r.url
        for line in r.iter_lines(chunk_size=16):
            print line

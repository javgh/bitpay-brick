#!/usr/bin/env python

import json
import requests
import threading

from retrying import retry

EVENT_ENDPOINT = 'https://bitpay.com/events'
CONTENT_TYPE_HEADER = {'content-type': 'text/event-stream'}
SUBSCRIBE_QUERY = 'action=subscribe&events%%5B%%5D=payment&token=%s'
STATUS_FIELD = 'status'
STATUS_EXPIRED = 'expired'
STATUS_PAID = 'paid'
STATUS_NO_CONNECTION = 'no connection'

class BitPayEventSource(threading.Thread):
    def __init__(self, token, callback, event_endpoint = EVENT_ENDPOINT,
            retrying = True):
        super(BitPayEventSource, self).__init__()
        self.token = token
        self.callback = callback
        self.event_endpoint = event_endpoint
        self.retrying = retrying
        self.is_active = True

    def run(self):
        if self.retrying:
            self.connect_with_retrying()
        else:
            try:
                self.connect()
            except requests.ConnectionError:
                self.callback(STATUS_NO_CONNECTION)

    def stop(self):
        self.is_active = False

    @retry(wait_exponential_multiplier=250, wait_exponential_max=30000) # ms
    def connect_with_retrying(self):
        self.connect()

    def connect(self):
        if not self.is_active:
            return

        params = SUBSCRIBE_QUERY % self.token
        r = requests.get(self.event_endpoint, headers=CONTENT_TYPE_HEADER,
                params=params, stream=True)
        for line in r.iter_lines(chunk_size=1):
            if not self.is_active:
                break

            if ':' not in line:
                continue

            (field, value) = line.strip().split(':', 1)
            field = field.strip()

            if field != "data":
                continue

            try:
                j = json.loads(value)
                if not STATUS_FIELD in j:
                    continue

                if j[STATUS_FIELD] == STATUS_EXPIRED:
                    self.callback(STATUS_EXPIRED)
                if j[STATUS_FIELD] == STATUS_PAID:
                    self.callback(STATUS_PAID)
            except ValueError:
                pass

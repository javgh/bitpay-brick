#!/usr/bin/env python

import BaseHTTPServer
import json
import threading
import time
import unittest

from Queue import Queue

from bitpayeventsource import BitPayEventSource, STATUS_EXPIRED, STATUS_PAID, \
        STATUS_NO_CONNECTION

TEST_PORT = 8481
TEST_ENDPOINT = 'http://127.0.0.1:8481/'
TEST_TOKEN = 'testtoken'
CONTENT_EXPIRED = {'status': 'expired'}
CONTENT_PAID = {'status': 'paid'}

class OneShotServer(threading.Thread):
    def __init__(self, port, json_content):
        super(OneShotServer, self).__init__()
        self.port = port
        self.json_content = json_content

    def run(self):
        server = BaseHTTPServer.HTTPServer(('127.0.0.1', self.port),
                OneShotHandler)
        server.json_content = self.json_content
        server.handle_request()

class OneShotHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.wfile.write('\ndata:%s\n' %
                json.dumps(self.server.json_content))

    def log_request(self, code):
        pass    # no logging

class Test(unittest.TestCase):
    def test_callback_fires_for_expired_invoice(self):
        one_shot_server = OneShotServer(TEST_PORT, CONTENT_EXPIRED)
        one_shot_server.start()
        q = Queue()
        event_source = BitPayEventSource(TEST_TOKEN,
                callback = lambda status:q.put(status),
                event_endpoint = TEST_ENDPOINT)
        event_source.start()
        status = q.get()
        self.assertEqual(status, STATUS_EXPIRED)

    def test_returns_no_connection_status_on_error_when_retrying_is_disabled(self):
        q = Queue()
        event_source = BitPayEventSource(TEST_TOKEN,
                callback = lambda status:q.put(status),
                event_endpoint = TEST_ENDPOINT, retrying = False)
        event_source.start()
        status = q.get()
        self.assertEqual(status, STATUS_NO_CONNECTION)

    def test_retries_on_connection_errors(self):
        q = Queue()
        event_source = BitPayEventSource(TEST_TOKEN,
                callback = lambda status:q.put(status),
                event_endpoint = TEST_ENDPOINT, retrying = True)
        event_source.start()
        time.sleep(0.1)
        one_shot_server = OneShotServer(TEST_PORT, CONTENT_EXPIRED)
        one_shot_server.start()
        status = q.get()
        self.assertEqual(status, STATUS_EXPIRED)

    def test_callback_for_paid_invoice_fires(self):
        one_shot_server = OneShotServer(TEST_PORT, CONTENT_PAID)
        one_shot_server.start()
        q = Queue()
        event_source = BitPayEventSource(TEST_TOKEN,
                callback = lambda status:q.put(status),
                event_endpoint = TEST_ENDPOINT)
        event_source.start()
        status = q.get()
        self.assertEqual(status, STATUS_PAID)

    def test_can_be_stopped(self):
        event_source = BitPayEventSource(TEST_TOKEN,
                callback = lambda status:status,
                event_endpoint = TEST_ENDPOINT)
        event_source.start()
        event_source.stop()

if __name__ == '__main__':
    unittest.main()

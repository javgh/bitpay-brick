#!/usr/bin/env python

import re
import requests

from bitpayeventsource import BitPayEventSource

API_URL = 'https://bitpay.com/api/'

API_ENDPOINT_RATES = 'rates'
CURRENCY_CODE_EUR = 'EUR'
API_ENDPOINT_INVOICE = 'invoice'
BITCOIN_URI_REGEX = '"bitcoin:[^"]*"'
EVENT_TOKEN_URL = 'https://bitpay.com/invoices/%s/events'

class BitPayProvider:
    def __init__(self, api_key='', api_url=API_URL):
        self.api_key = api_key
        self.api_url = api_url

    def get_euro_rate(self):
        r = requests.get(self.api_url + API_ENDPOINT_RATES)
        rates = r.json()
        for rate in rates:
            if rate['code'] == CURRENCY_CODE_EUR:
                return rate['rate']
        raise Exception('Euro rate not provided.')

    def create_invoice(self, price, currency, item_desc=None, marker=None):
        payload = {'price': price, 'currency': currency}
        if item_desc:
            payload['itemDesc'] = item_desc
        if marker:
            payload['posData'] = marker
        r = requests.post(self.api_url + API_ENDPOINT_INVOICE, data=payload,
                auth=(self.api_key, ''))
        json = r.json()
        if 'error' in json:
            raise Exception(json['error']['message'])
        invoice = BitPayInvoice.construct_from_json(json)
        return invoice

class BitPayInvoice:
    def __init__(self, invoice_id, url, status, bitcoin_uri, event_token):
        self.invoice_id = invoice_id
        self.url = url
        self.status = status
        self.bitcoin_uri = bitcoin_uri
        self.event_token = event_token
        self.event_source = BitPayEventSource(event_token, callback =
                self._status_callback)

    def get_url(self):
        return self.url

    def get_bitcoin_uri(self):
        return self.bitcoin_uri

    def get_event_token(self):
        return self.event_token

    def watch(self, callback):
        """Start a thread that will watch the invoice for status updates. The
        callback will be called with a new status in the form of one of the
        strings defined in the module bitpayeventsource."""
        self.callback = callback
        self.event_source.start()

    def stop_watching(self):
        self.event_source.stop()

    def _status_callback(self, status):
        self.callback(status)

    @staticmethod
    def construct_from_json(json):
        invoice_id = json['id']
        url = json['url']
        status = json['status']

        r = requests.get(url)
        match = re.search(BITCOIN_URI_REGEX, r.text)
        if not match:
            raise Exception("Unable to extract Bitcoin URI")

        bitcoin_uri = match.group(0)
        bitcoin_uri = bitcoin_uri.replace('"', '').replace('&amp;', '&')

        r2 = requests.get(EVENT_TOKEN_URL % invoice_id)
        json = r2.json()
        if not 'data' in json or not 'token' in json['data']:
            raise Exception("Unable to get event token")
        event_token = json['data']['token']

        return BitPayInvoice(invoice_id, url, status, bitcoin_uri, event_token)

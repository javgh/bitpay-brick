#!/usr/bin/env python

import re
import requests

API_URL = 'https://bitpay.com/api/'

API_ENDPOINT_RATES = 'rates'
CURRENCY_CODE_EUR = 'EUR'
API_ENDPOINT_INVOICE = 'invoice'
BITCOIN_URI_REGEX = '"bitcoin:[^"]*"'

class BitPayProvider:
    def __init__(self, api_key='', api_url=API_URL):
        self.api_key = api_key
        self.api_url = api_url

    def get_euro_rate(self):
        r = requests.get(self.api_url + API_ENDPOINT_RATES)
        rates = r.json
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
        if 'error' in r.json:
            raise Exception(r.json['error']['message'])
        invoice = BitPayInvoice.construct_from_json(r.json)
        return invoice

class BitPayInvoice:
    def __init__(self, invoice_id, url, status, bitcoin_uri):
        self.invoice_id = invoice_id
        self.url = url
        self.status = status
        self.bitcoin_uri = bitcoin_uri

    def get_url(self):
        return self.url

    def get_bitcoin_uri(self):
        return self.bitcoin_uri

    @staticmethod
    def construct_from_json(json):
        invoice_id = json['id']
        url = json['url']
        status = json['status']

        r = requests.get(url)
        match = re.search(BITCOIN_URI_REGEX, r.text)
        if match:
            bitcoin_uri = match.group(0)
            bitcoin_uri = bitcoin_uri.replace('"', '').replace('&amp;', '&')
            return BitPayInvoice(invoice_id, url, status, bitcoin_uri)
        else:
            raise Exception("Unable to extract Bitcoin URI")

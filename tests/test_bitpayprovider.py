#!/usr/bin/env python

import requests
import sys
import unittest

from os.path import expanduser, isfile

from bitpayprovider import BitPayProvider

TEST_API_KEY_FILE = '.bitpay-brick-test-api-key'
API_URL_WITH_IP = 'https://141.101.113.162/api/'

def read_test_api_key():
    api_key_file = expanduser('~') + '/' + TEST_API_KEY_FILE
    if not isfile(api_key_file):
        return None
    with open(api_key_file, 'r') as f:
        api_key = f.read()
    return api_key.strip()

TEST_API_KEY = read_test_api_key()

class Test(unittest.TestCase):
    def test_rejects_connection_without_verified_certificate(self):
        bitpay_provider = BitPayProvider('', API_URL_WITH_IP)
        with self.assertRaises(requests.exceptions.SSLError):
            bitpay_provider.get_euro_rate()

    def test_current_euro_rate_is_nonzero(self):
        bitpay_provider = BitPayProvider()
        euro_rate = bitpay_provider.get_euro_rate()
        self.assertTrue(euro_rate != 0)

    def test_creating_an_invoice_without_a_key_fails(self):
        bitpay_provider = BitPayProvider()
        with self.assertRaises(Exception):
            bitpay_provider.create_invoice(42, 'EUR')

    @unittest.skipUnless(TEST_API_KEY != None, "no API key available")
    def test_creating_a_simple_invoice_is_possible(self):
        bitpay_provider = BitPayProvider(TEST_API_KEY)
        invoice = bitpay_provider.create_invoice(0.05, 'EUR')
        self.assertTrue(invoice.get_url().startswith('https://bitpay.com'),
                "no BitPay URL provided for invoice")

    @unittest.skipUnless(TEST_API_KEY != None, "no API key available")
    def test_created_invoice_knows_its_bitcoin_uri(self):
        bitpay_provider = BitPayProvider(TEST_API_KEY)
        invoice = bitpay_provider.create_invoice(42, 'EUR')
        self.assertTrue(invoice.get_bitcoin_uri().startswith('bitcoin:'))

    @unittest.skipUnless(TEST_API_KEY != None, "no API key available")
    def test_created_invoice_knows_its_event_token(self):
        bitpay_provider = BitPayProvider(TEST_API_KEY)
        invoice = bitpay_provider.create_invoice(42, 'EUR')
        self.assertTrue(len(invoice.get_event_token()) > 16)

    @unittest.skipUnless(TEST_API_KEY != None, "no API key available")
    def test_can_watch_and_stop_watching_an_invoice(self):
        bitpay_provider = BitPayProvider(TEST_API_KEY)
        invoice = bitpay_provider.create_invoice(42, 'EUR')
        invoice.watch(callback = lambda status:status)
        invoice.stop_watching()

if __name__ == '__main__':
    unittest.main()

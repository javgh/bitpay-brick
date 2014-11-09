#!/usr/bin/env python

from bitpayprovider import BitPayProvider
from config import read_api_key

api_key = read_api_key()
if not api_key:
    raise Exception("Unable to load API key.")

bitpay_provider = BitPayProvider(api_key)
invoice = bitpay_provider.create_invoice(0.01, 'EUR')

print "URL: %s" % invoice.get_url()
print "Bitcoin URI: %s" % invoice.get_bitcoin_uri()
print "Event token: %s" % invoice.get_event_token()

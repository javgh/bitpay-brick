#!/usr/bin/env python

import readline

from os.path import expanduser, isfile

from bitpayprovider import BitPayProvider
from frontend import Frontend
from invoicer import Invoicer
from nfcbroadcast import NFCBroadcast

API_KEY_FILE = '.bitpay-brick-api-key'
DEFAULT_CURRENCY = 'EUR'

def read_api_key():
    api_key_file = expanduser('~') + '/' + API_KEY_FILE
    if not isfile(api_key_file):
        return None
    with open(api_key_file, 'r') as f:
        api_key = f.read()
    return api_key.strip()

api_key = read_api_key()
bitpay_provider = BitPayProvider(api_key)
frontend = Frontend()
frontend.start()
nfc_broadcast = NFCBroadcast()
nfc_broadcast.start()
invoicer = Invoicer(bitpay_provider, frontend, nfc_broadcast)

try:
    while True:
        price = raw_input('Price for new invoice in %s or Ctrl-D to exit: ' % DEFAULT_CURRENCY)
        price_float = float(price)
        invoicer.new_invoice(price, DEFAULT_CURRENCY)
except EOFError:
    pass

frontend.shutdown()
nfc_broadcast.shutdown()

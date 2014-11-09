#!/usr/bin/env python

import readline

from bitpayprovider import BitPayProvider
from config import read_api_key
from frontend import Frontend
from invoicer import Invoicer
from nfcbroadcast import NFCBroadcast

DEFAULT_CURRENCY = 'EUR'

api_key = read_api_key()
if not api_key:
    raise Exception("Unable to load API key.")

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

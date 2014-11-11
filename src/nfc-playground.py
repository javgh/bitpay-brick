#!/usr/bin/env python

from bitpayprovider import BitPayProvider
from bluetoothservice import BluetoothPaymentRequestService
from config import read_api_key
from nfcbroadcast import NFCBroadcast

api_key = read_api_key()
if not api_key:
    raise Exception("Unable to load API key.")

bitpay_provider = BitPayProvider(api_key)
invoice = bitpay_provider.create_invoice(0.01, 'EUR')

print "URL: %s" % invoice.get_url()
print "Bitcoin URI: %s" % invoice.get_bitcoin_uri()

payment_request_service = \
        BluetoothPaymentRequestService(invoice.get_payment_request())
payment_request_service.start()
bt_addr = payment_request_service.get_bluetooth_address()
btc_uri = invoice.get_bitcoin_uri()
btc_uri = btc_uri[0:btc_uri.find('&r=')]
btc_uri = btc_uri + "&r=bt:%s" % bt_addr.replace(':', '')
print bt_addr
print btc_uri

nfc_broadcast = NFCBroadcast()
nfc_broadcast.start()
nfc_broadcast.set_btc_uri(btc_uri)

raw_input("Press return to exit")

nfc_broadcast.shutdown()

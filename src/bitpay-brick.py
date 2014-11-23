#!/usr/bin/env python

import readline

from Queue import Queue

from bitpayeventsource import STATUS_PAID
from bitpayprovider import BitPayProvider
from bluetoothservice import BluetoothPaymentRequestService, \
        BluetoothTxSubmissionService
from config import read_api_key
from frontend import Frontend
from nfcbroadcast import NFCBroadcast

DEFAULT_CURRENCY = 'EUR'
DEFAULT_AMOUNT = 0.10

api_key = read_api_key()
if not api_key:
    raise Exception("Unable to load API key.")

bitpay_provider = BitPayProvider(api_key)

nfc_broadcast = NFCBroadcast()
nfc_broadcast.start()

invoice_queue = Queue()
def new_invoice_requested():
    invoice_queue.put(None)

frontend = Frontend(frontend_type = Frontend.TYPE_FRONTEND_SMALL_DISPLAY,
        invoice_request_callback=new_invoice_requested)
frontend.start()

invoice_queue.get() # wait until user initiates a new invoice

invoice = bitpay_provider.create_invoice(DEFAULT_AMOUNT, DEFAULT_CURRENCY)

payment_request_service = \
        BluetoothPaymentRequestService(invoice.get_payment_request())
payment_request_service.start()
tx_submission_service = BluetoothTxSubmissionService(invoice.get_bip70_url())
tx_submission_service.start()

bluetooth_address = tx_submission_service.get_bluetooth_address()

nfc_broadcast.set_btc_uri(
        invoice.get_bitcoin_uri_with_bluetooth_address(bluetooth_address))

def check_status(status):
    if (status == STATUS_PAID):
        frontend.show_paid()
invoice.watch(check_status)

frontend.show_invoice(invoice.get_bitcoin_uri())
print invoice.get_url()
raw_input("Press return to exit")

frontend.shutdown()
invoice.stop_watching()
nfc_broadcast.shutdown()
payment_request_service.stop()
tx_submission_service.stop()

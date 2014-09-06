#!/usr/bin/env python

DEFAULT_CURRENCY = 'EUR'

class Invoicer:
    def __init__(self, bitpay_provider, frontend, nfc_broadcast):
        self.bitpay_provider = bitpay_provider
        self.frontend = frontend
        self.nfc_broadcast = nfc_broadcast

    def new_invoice(self, price):
        invoice = self.bitpay_provider.create_invoice(price, DEFAULT_CURRENCY)
        self.frontend.show_invoice(invoice.get_url())
        self.nfc_broadcast.set_btc_uri(invoice.get_bitcoin_uri())

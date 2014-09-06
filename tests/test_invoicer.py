#!/usr/bin/env python

import unittest

from mock import create_autospec, ANY

from bitpayprovider import BitPayProvider, BitPayInvoice
from frontend import Frontend
from invoicer import Invoicer
from nfcbroadcast import NFCBroadcast

class Test(unittest.TestCase):
    def setUp(self):
        self.bitpay_provider = create_autospec(BitPayProvider)
        self.frontend = create_autospec(Frontend)
        self.nfc_broadcast = create_autospec(NFCBroadcast)

    def test_new_invoice_is_displayed_and_broadcasted_via_nfc(self):
        self.bitpay_provider.create_invoice.return_value = \
                create_autospec(BitPayInvoice)

        invoicer = Invoicer(self.bitpay_provider, self.frontend,
                self.nfc_broadcast)
        invoicer.new_invoice(42)

        self.bitpay_provider.create_invoice.assert_called_with(ANY, ANY)
        self.frontend.show_invoice.assert_called_with(ANY)
        self.nfc_broadcast.set_btc_uri.assert_called_with(ANY)

if __name__ == '__main__':
    unittest.main()

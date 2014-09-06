#!/usr/bin/env python

import unittest

from frontend import Frontend

INVOICE = 'https://bitpay.com/invoice?id=8FXiinBvNWM9THj4T93Jsz'

class Test(unittest.TestCase):
    def test_can_be_started_and_stopped(self):
        frontend = Frontend(Frontend.TYPE_FRONTEND_INVISIBLE)
        frontend.start()
        frontend.shutdown()

    def test_can_show_invoice(self):
        frontend = Frontend(Frontend.TYPE_FRONTEND_INVISIBLE)
        frontend.start()
        frontend.show_invoice(INVOICE)
        invoice = frontend.get_current_invoice()
        frontend.shutdown()
        self.assertEqual(INVOICE, invoice)

if __name__ == '__main__':
    unittest.main()

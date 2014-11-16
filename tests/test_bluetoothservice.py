#!/usr/bin/env python

import unittest

from bluetoothservice import BluetoothPaymentRequestService, \
        BluetoothTxSubmissionService

class Test(unittest.TestCase):
    def test_payment_request_service_can_be_started_and_stopped(self):
        payment_request_service = BluetoothPaymentRequestService(None)
        payment_request_service.start()
        payment_request_service.stop()

    def test_tx_submission_service_can_be_started_and_stopped(self):
        tx_submission_service = BluetoothTxSubmissionService(None)
        tx_submission_service.start()
        tx_submission_service.stop()

    def test_payment_request_service_knows_its_bluetooth_address(self):
        payment_request_service = BluetoothPaymentRequestService(None)
        payment_request_service.start()
        bluetooth_address = payment_request_service.get_bluetooth_address()
        payment_request_service.stop()
        self.assertIn(':', bluetooth_address)
        self.assertEqual(len(bluetooth_address), 17)

if __name__ == '__main__':
    unittest.main()

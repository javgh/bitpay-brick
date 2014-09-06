#!/usr/bin/env python

import unittest

from multiprocessing import Process, Queue

from nfcbroadcast import NFCBroadcast

BITCOIN_URI = 'bitcoin:16mj2Veiw6rWHBDn4dN8rAAsRJog7EooYF?amount=0.0001'

class CheckNFCAvailability(Process):
    def __init__(self, queue):
        self.queue = queue
        super(CheckNFCAvailability, self).__init__()

    def run(self):
        nfc_broadcast = NFCBroadcast()
        nfc_broadcast.start()
        is_available = nfc_broadcast.is_nfc_available()
        nfc_broadcast.shutdown()
        self.queue.put(is_available)

def is_nfc_available():
    # not sure why exactly, but running this check as part
    # of test preparation apparently needs to happen in a
    # separate process, as things block otherwise
    answer_queue = Queue()
    check_nfc_availability = CheckNFCAvailability(answer_queue)
    check_nfc_availability.start()
    return answer_queue.get()

HAS_NFC = is_nfc_available()

class Test(unittest.TestCase):
    def test_can_be_started_and_stopped(self):
        nfc_broadcast = NFCBroadcast()
        nfc_broadcast.start()
        nfc_broadcast.shutdown()

    def test_nfc_availability_can_be_queried(self):
        nfc_broadcast = NFCBroadcast()
        nfc_broadcast.start()
        nfc_broadcast.is_nfc_available()
        nfc_broadcast.shutdown()

    @unittest.skipUnless(HAS_NFC, "no NFC hardware available")
    def test_bitcoin_uri_can_be_set(self):
        nfc_broadcast = NFCBroadcast()
        nfc_broadcast.start()
        nfc_broadcast.set_btc_uri(BITCOIN_URI)
        nfc_broadcast.shutdown()

if __name__ == '__main__':
    unittest.main()

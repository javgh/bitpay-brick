#!/usr/bin/env python

# NFC communication is implemented in its own process and a queue is used to
# communicate across process boundaries and submit the current Bitcoin URI to be
# broadcasted via NFC. Originally this was done to prevent the Qt event loop
# from interfering with NFC.

import threading
import time

from multiprocessing import Process, Queue

import nfc
import nfc.snep

CMD_IS_NFC_AVAILBLE = 'availability'
CMD_SET_BTC_URI = 'uri'
CMD_SHUTDOWN = 'shutdown'

class NFCBroadcast:
    def start(self):
        self.queue = Queue()
        self.backchannel = Queue()
        self.nfc_process = NFCProcess(self.queue, self.backchannel)
        self.nfc_process.start()

    def is_nfc_available(self):
        self.queue.put((CMD_IS_NFC_AVAILBLE, None))
        return self.backchannel.get()

    def set_btc_uri(self, btc_uri):
        self.queue.put((CMD_SET_BTC_URI, btc_uri))

    def shutdown(self):
        self.queue.put((CMD_SHUTDOWN, None))
        self.backchannel.get()  # wait for command to be processed

class NFCProcess(Process):
    def __init__(self, queue, backchannel):
        self.queue = queue
        self.backchannel = backchannel
        super(NFCProcess, self).__init__()

    def run(self):
        nfc_conn = NFCConnection()
        nfc_conn.start()

        is_running = True
        while is_running:
            (cmd, param) = self.queue.get()
            if cmd == CMD_SET_BTC_URI:
                nfc_conn.set_btc_uri(param)
            elif cmd == CMD_IS_NFC_AVAILBLE:
                answer = nfc_conn.is_nfc_available()
                self.backchannel.put(answer)
            elif cmd == CMD_SHUTDOWN:
                is_running = False
                self.backchannel.put(None)

class NFCConnection(threading.Thread):
    def __init__(self):
        self.btc_uri = None
        self.restart_required = False
        self.start_signal = Queue()
        try:
            self.clf = nfc.ContactlessFrontend('usb')
            print "NFC hardware ready"
        except IOError:
            self.clf = None
            print "No NFC hardware found"
        super(NFCConnection, self).__init__()

    def run(self):
        # wait for first URI
        _ = self.start_signal.get()

        if self.clf:
            self.serve_nfc()
        else:
            self.idle_forever()

    def serve_nfc(self):
        print "NFC hardware active"
        while True:
            self.clf.connect( llcp={'on-connect': self.connected}
                            , terminate=self.check_restart
                            )

    def idle_forever(self):
        while True:
            time.sleep(60)

    def is_nfc_available(self):
        return self.clf != None

    def set_btc_uri(self, btc_uri):
        if self.btc_uri == None:
            self.btc_uri = btc_uri
            self.start_signal.put('start')
        else:
            self.btc_uri = btc_uri
            self.restart_required = True

    def connected(self, llc):
        self.helper = NFCConnectionHelper(llc, self.btc_uri)
            # store reference to thread beyond the local function
            # to prevent if from being garbage collected
        self.helper.start()
        return True

    def check_restart(self):
        if self.restart_required:
            self.restart_required = False
            return True
        else:
            return False

class NFCConnectionHelper(threading.Thread):
    def __init__(self, llc, btc_uri):
        self.llc = llc
        self.btc_uri = btc_uri
        super(NFCConnectionHelper, self).__init__()

    def run(self):
        sp = nfc.ndef.SmartPosterRecord(self.btc_uri)
        snep = nfc.snep.SnepClient(self.llc)
        snep.put(nfc.ndef.Message(sp))

#!/usr/bin/env python

import binascii
import errno
import requests
import select
import socket
import struct
import threading
import time

import bluetooth._bluetooth as _bt

from bluetooth import *
from Queue import Queue

from paymentrequest_pb2 import PaymentACK, PaymentDetails, PaymentRequest

PAYMENT_REQUESTS_DESC = "Bitcoin BIP70 payment requests"
PAYMENT_REQUESTS_UUID = "3357a7bb-762d-464a-8d9a-dca592d57d59"

TX_SUBMISSION_DESC = "Bitcoin BIP70 tx submission"
TX_SUBMISSION_UUID = "3357a7bb-762d-464a-8d9a-dca592d57d5a"

TX_SUBMISSION_HEADERS = { 'content-type': 'application/bitcoin-payment'
                        , 'accept': 'application/bitcoin-paymentack'
                        }

SELECT_LOOP_INTERVAL = 0.1      # 100 ms

def read_varint32(sock):
    mask = (1 << 32) - 1
    result = 0
    shift = 0
    while True:
        unpacker = struct.Struct('! B')
        data = sock.recv(unpacker.size, socket.MSG_WAITALL)
        (b,) = unpacker.unpack(data)

        result |= ((b & 0x7f) << shift)
        if not (b & 0x80):
            result &= mask
            return result
        shift += 7
        if shift >= 64:
            raise IOError("Too many bytes when decoding varint.")

def write_varint32(sock, value):
    bits = value & 0x7f
    value >>= 7
    while value:
        packer = struct.Struct('! B')
        packed_data = packer.pack(0x80|bits)
        sock.send(packed_data)
        bits = value & 0x7f
        value >>= 7
    packer = struct.Struct('! B')
    packed_data = packer.pack(bits)
    sock.send(packed_data)

class BluetoothService(threading.Thread):
    def __init__(self, service_desc, service_uuid):
        self.service_desc = service_desc
        self.service_uuid = service_uuid
        self.bt_addr = None
        self.bt_addr_queue = Queue()
        self.is_active = True
        super(BluetoothService, self).__init__()

    def _find_local_bdaddr(self):
        dev_id = 0
        hci_sock = _bt.hci_open_dev(dev_id)

        old_filter = hci_sock.getsockopt( _bt.SOL_HCI, _bt.HCI_FILTER, 14)
        flt = _bt.hci_filter_new()
        opcode = _bt.cmd_opcode_pack(_bt.OGF_INFO_PARAM, _bt.OCF_READ_BD_ADDR)
        _bt.hci_filter_set_ptype(flt, _bt.HCI_EVENT_PKT)
        _bt.hci_filter_set_event(flt, _bt.EVT_CMD_COMPLETE);
        _bt.hci_filter_set_opcode(flt, opcode)
        hci_sock.setsockopt(_bt.SOL_HCI, _bt.HCI_FILTER, flt)

        _bt.hci_send_cmd(hci_sock, _bt.OGF_INFO_PARAM, _bt.OCF_READ_BD_ADDR)

        pkt = hci_sock.recv(255)

        status,raw_bdaddr = struct.unpack("xxxxxxB6s", pkt)
        assert status == 0

        t = [ "%X" % ord(b) for b in raw_bdaddr ]
        t.reverse()
        bdaddr = ":".join(t)

        # restore old filter
        hci_sock.setsockopt( _bt.SOL_HCI, _bt.HCI_FILTER, old_filter )
        return bdaddr

    def _init_server(self):
        # find our Bluetooth address
        self.bt_addr = self._find_local_bdaddr()
        self.bt_addr_queue.put(None)

        # find a free port; PORT_ANY does not seem to work correctly
        port_available = False
        server_sock = BluetoothSocket(RFCOMM)
        for port in range(1, 10):
            try:
                server_sock.bind((self.bt_addr, port))
                port_available = True
                break
            except Exception as e:  # IOError does not seem to catch the right exception
                if e[0] == errno.EADDRINUSE:
                    pass
                else:
                    raise e

        if not port_available:
            print 'No free bluetooth port found'
            return None

        server_sock.listen(1)
        port = server_sock.getsockname()[1]

        advertise_service( server_sock, self.service_desc
                         , service_id = self.service_uuid
                         , service_classes = [ self.service_uuid ]
                         , profiles = [ ]
                         )

        return server_sock

    def get_bluetooth_address(self):
        """Return active Bluetooth address and block until the address is
        available. You need to call start() first."""
        if not self.bt_addr:
            self.bt_addr_queue.get()
        return self.bt_addr

    def run(self):
        raise Exception("Missing implementation")

class BluetoothPaymentRequestService(BluetoothService):
    def __init__(self, payment_request):
        self.serialized_payment_request = payment_request
        super(BluetoothPaymentRequestService, self).__init__(
                PAYMENT_REQUESTS_DESC, PAYMENT_REQUESTS_UUID)

    def run(self):
        server_sock = self._init_server()
        server_sock.setblocking(0)

        while self.is_active:
            (rlist, _, _) = select.select(
                    [server_sock], [], [], SELECT_LOOP_INTERVAL)

            if len(rlist) == 0:
                continue

            client_sock, client_info = server_sock.accept()
            print "Accepted connection from ", client_info
            try:
                # header: a single '0' and then the length of the request string
                just_zero = read_varint32(client_sock)
                request_length = read_varint32(client_sock)

                if just_zero != 0:
                    raise IOError

                if request_length > 2 ** 24:
                    raise IOError

                # request string
                unpacker = struct.Struct('! %ss' % request_length)
                body = client_sock.recv(unpacker.size, socket.MSG_WAITALL)
                request = unpacker.unpack(body)

                # send ok
                write_varint32(client_sock, 200)

                # monkey patch the payment request
                # to include our Bluetooth address
                payment_request = PaymentRequest()
                payment_request.ParseFromString(self.serialized_payment_request)
                payment_details = PaymentDetails()
                payment_details.ParseFromString(
                        payment_request.serialized_payment_details)
                payment_details.payment_url = 'bt:%s' % \
                        self.bt_addr.replace(':', '')
                payment_request.serialized_payment_details = \
                        payment_details.SerializeToString()
                payment_request.ClearField('pki_type')
                payment_request.ClearField('pki_data')
                payment_request.ClearField('signature')
                data = payment_request.SerializeToString()

                # send payment request
                write_varint32(client_sock, len(data))
                client_sock.send(data)
            except IOError:
                pass

            print "Bluetooth client disconnected"
            client_sock.close()
        server_sock.close()

    def stop(self):
        self.is_active = False
        self.join()

class BluetoothTxSubmissionService(BluetoothService):
    def __init__(self, submission_url):
        self.submission_url = submission_url
        super(BluetoothTxSubmissionService, self).__init__(
                TX_SUBMISSION_DESC, TX_SUBMISSION_UUID)

    def run(self):
        server_sock = self._init_server()
        server_sock.setblocking(0)

        while self.is_active:
            (rlist, _, _) = select.select(
                    [server_sock], [], [], SELECT_LOOP_INTERVAL)

            if not rlist:
                continue

            client_sock, client_info = server_sock.accept()
            print "Accepted connection from ", client_info
            try:
                # read length
                tx_length = read_varint32(client_sock)
                if tx_length > 2 ** 24:
                    raise IOError

                # transaction
                unpacker = struct.Struct('! %ss' % tx_length)
                body = client_sock.recv(unpacker.size, socket.MSG_WAITALL)
                (tx,) = unpacker.unpack(body)

                # submit
                r = requests.post(self.submission_url,
                        headers=TX_SUBMISSION_HEADERS, data=tx)

                # monkey patch ack
                payment_ack = PaymentACK()
                payment_ack.ParseFromString(r.content)
                payment_ack.memo = "ack"
                payment_ack_data = payment_ack.SerializeToString()

                # pass on ack
                write_varint32(client_sock, len(payment_ack_data))
                client_sock.send(payment_ack_data)
            except IOError:
                pass

            print "Bluetooth client disconnected"
            client_sock.close()
        server_sock.close()

    def stop(self):
        self.is_active = False
        self.join()

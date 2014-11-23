#!/usr/bin/env python

import unittest

from Queue import Queue

from frontend import Frontend

class Test(unittest.TestCase):
    def test_can_be_started_and_stopped_and_defaults_to_idle(self):
        frontend = Frontend(Frontend.TYPE_FRONTEND_INVISIBLE)
        frontend.start()
        active_div = frontend.get_active_div()
        frontend.shutdown()
        self.assertEqual(active_div, "#idle")

    def test_can_show_status_as_paid(self):
        frontend = Frontend(Frontend.TYPE_FRONTEND_INVISIBLE)
        frontend.start()
        frontend.show_paid()
        active_div = frontend.get_active_div()
        frontend.shutdown()
        self.assertEqual(active_div, "#paid")

    def test_can_switch_to_paid_and_back_to_idle(self):
        frontend = Frontend(Frontend.TYPE_FRONTEND_INVISIBLE)
        frontend.start()
        frontend.show_paid()
        active_div = frontend.get_active_div()
        frontend.show_idle()
        active_div2 = frontend.get_active_div()
        frontend.shutdown()
        self.assertEqual(active_div, "#paid")
        self.assertEqual(active_div2, "#idle")

    def test_can_show_invoice(self):
        frontend = Frontend(Frontend.TYPE_FRONTEND_INVISIBLE)
        frontend.start()
        frontend.show_invoice('bitcoin:1asdf')
        active_div = frontend.get_active_div()
        frontend.shutdown()
        self.assertEqual(active_div, "#invoice")

    def test_user_can_initiate_new_invoice(self):
        q = Queue()
        def request_received():
            q.put(None)

        frontend = Frontend(Frontend.TYPE_FRONTEND_INVISIBLE,
                invoice_request_callback=request_received)
        frontend.start()
        frontend.exercise_javascript_bridge()
        q.get()
        frontend.shutdown()

if __name__ == '__main__':
    unittest.main()

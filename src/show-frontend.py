#!/usr/bin/env python

from frontend import Frontend

def show_msg():
    print "Request for a new invoice"

frontend = Frontend(frontend_type = Frontend.TYPE_FRONTEND_SMALL_DISPLAY,
        invoice_request_callback=show_msg)
frontend.start()

raw_input("Press return to perform transition")

frontend.show_paid()

raw_input("Press return to exit")

frontend.shutdown()

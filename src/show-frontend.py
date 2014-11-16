#!/usr/bin/env python

from frontend import Frontend

frontend = Frontend(frontend_type = Frontend.TYPE_FRONTEND_SMALL_DISPLAY)
frontend.start()

raw_input("Press return to perform transition")

frontend.show_paid()

raw_input("Press return to exit")

frontend.shutdown()

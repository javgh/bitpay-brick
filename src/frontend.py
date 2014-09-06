#!/usr/bin/env python

# The Qt frontend runs in its own process, as the Qt event loop
# wants to sit on the main thread.

import threading
import time

from multiprocessing import Process, Queue
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.Qt import QThread
from PyQt4.QtWebKit import QWebView

FRONTEND_HTML = 'data/customer_display.html'
FRONTEND_WINDOW_TITLE = 'BitPay Brick'

CMD_SHOW_INVOICE = 'show_invoice'
CMD_GET_CURRENT_INVOICE = 'get_current_invoice'
CMD_SHUTDOWN = 'shutdown'

class Frontend:
    TYPE_FRONTEND_STANDARD = 0
    TYPE_FRONTEND_INVISIBLE = 1

    def __init__(self, frontend_type=TYPE_FRONTEND_STANDARD):
        self.frontend_type = frontend_type

    def start(self):
        self.queue = Queue()
        self.backchannel = Queue()
        self.frontend_process = FrontendProcess(self.frontend_type,
                self.queue, self.backchannel)
        self.frontend_process.start()

    def show_invoice(self, url):
        self.queue.put((CMD_SHOW_INVOICE, url))
        self.backchannel.get()  # block until command is processed

    def get_current_invoice(self):
        self.queue.put((CMD_GET_CURRENT_INVOICE, None))
        return self.backchannel.get()

    def shutdown(self):
        self.queue.put((CMD_SHUTDOWN, None))

class CmdListener(threading.Thread):
    def __init__(self, frontend_process, queue, backchannel, ready_for_cmds):
        self.frontend_process = frontend_process
        self.queue = queue
        self.backchannel = backchannel
        self.ready_for_cmds = ready_for_cmds
        super(CmdListener, self).__init__()

    def run(self):
        self.ready_for_cmds.wait()
        is_running = True
        while is_running:
            (cmd, param) = self.queue.get()
            if cmd == CMD_SHOW_INVOICE:
                self.frontend_process.show_invoice(param)
                self.backchannel.put(None)
            elif cmd == CMD_GET_CURRENT_INVOICE:
                answer = self.frontend_process.get_current_invoice()
                self.backchannel.put(answer)
            elif cmd == CMD_SHUTDOWN:
                self.frontend_process.shutdown()
                is_running = False

class FrontendProcess(Process):
    def __init__(self, frontend_type, queue, backchannel):
        self.frontend_type = frontend_type
        self.queue = queue
        self.backchannel = backchannel
        super(FrontendProcess, self).__init__()

    def run(self):
        self.app = QtGui.QApplication([])

        ready_for_cmds = threading.Event()
        self.display = Display(FRONTEND_HTML, ready_for_cmds)
        if (self.frontend_type != Frontend.TYPE_FRONTEND_INVISIBLE):
            self.display.show()

        self.app.connect(self.app, QtCore.SIGNAL('_show_invoice(PyQt_PyObject)'),
                self._show_invoice)
        self.app.connect(self.app, QtCore.SIGNAL('_get_current_invoice(PyQt_PyObject)'),
                self._get_current_invoice)
        self.app.connect(self.app, QtCore.SIGNAL('_shutdown()'),
                self._shutdown)

        # init complete; start listening for commands when the page is ready
        self.cmd_listener = CmdListener(self, self.queue, self.backchannel,
                ready_for_cmds)
        self.cmd_listener.start()

        self.app.exec_()

    def show_invoice(self, url):
        self.app.emit(QtCore.SIGNAL('_show_invoice(PyQt_PyObject)'), url)

    def _show_invoice(self, url):
        self.display.show_invoice(url)

    def get_current_invoice(self):
        answer_queue = Queue()
        self.app.emit(QtCore.SIGNAL('_get_current_invoice(PyQt_PyObject)'), answer_queue)
        return answer_queue.get()

    def _get_current_invoice(self, answer_queue):
        answer = self.display.get_current_invoice()
        answer_queue.put(answer)

    def shutdown(self):
        self.app.emit(QtCore.SIGNAL('_shutdown()'))

    def _shutdown(self):
        QtGui.QApplication.exit()

class Display(QWebView):
    def __init__(self, page, ready_for_cmds):
        QWebView.__init__(self)
        self.setWindowTitle(FRONTEND_WINDOW_TITLE)
        self.ready_for_cmds = ready_for_cmds
        self.page().loadFinished.connect(self.page_is_ready)
        self.load(QtCore.QUrl(page))

    def page_is_ready(self):
        self.ready_for_cmds.set()

    def show_invoice(self, url):
        self._evaluate_java_script('show_invoice("%s")' % url)

    def get_current_invoice(self):
        return self._evaluate_java_script('get_current_invoice()').toString()

    def _evaluate_java_script(self, js):
        return self.page().mainFrame().evaluateJavaScript(js)

    def closeEvent(self, event):
        event.accept()
        QtGui.QApplication.exit()

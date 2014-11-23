#!/usr/bin/env python

# The Qt frontend runs in its own process, as the Qt event loop
# wants to sit on the main thread.

import qrencode
import threading
import time
import urllib

from multiprocessing import Process, Queue
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtWebKit import QWebView
from StringIO import StringIO

FRONTEND_HTML = 'data/customer_display.html'
FRONTEND_WINDOW_TITLE = 'BitPay Brick'

CMD_SHOW_IDLE = 'show_idle'
CMD_SHOW_INVOICE = 'show_invoice'
CMD_SHOW_PAID = 'show_paid'
CMD_GET_ACTIVE_DIV = 'get_active_div'
CMD_SHUTDOWN = 'shutdown'
CMD_EXERCISE_JAVASCRIPT_BRIDGE = 'exercise_javascript_bridge'
CMD_CALLBACK = 'callback'

SMALL_DISPLAY_WIDTH = 320
SMALL_DISPLAY_HEIGHT = 240

QR_CODE_SIZE = 220

class Frontend:
    TYPE_FRONTEND_STANDARD = 0
    TYPE_FRONTEND_INVISIBLE = 1
    TYPE_FRONTEND_SMALL_DISPLAY = 2
    TYPE_FRONTEND_FULLSCREEN = 3

    def __init__(self, frontend_type=TYPE_FRONTEND_STANDARD,
            invoice_request_callback=None):
        self.invoice_request_callback = invoice_request_callback
        self.frontend_type = frontend_type
        self.invoice_request_queue = Queue()

    def start(self):
        self.queue = Queue()
        self.backchannel = Queue()
        if self.invoice_request_callback:
            self.invoice_request_listener = \
                    InvoiceRequestListener(self.invoice_request_queue,
                            self.invoice_request_callback)
            self.invoice_request_listener.start()
        self.frontend_process = FrontendProcess(self.frontend_type,
                self.queue, self.backchannel,
                self.invoice_request_queue)
        self.frontend_process.start()

    def show_invoice(self, bitcoin_uri):
        self.queue.put((CMD_SHOW_INVOICE, bitcoin_uri))
        self.backchannel.get()  # block until command is processed

    def show_idle(self):
        self.queue.put((CMD_SHOW_IDLE, None))
        self.backchannel.get()

    def show_paid(self):
        self.queue.put((CMD_SHOW_PAID, None))
        self.backchannel.get()

    def get_active_div(self):
        self.queue.put((CMD_GET_ACTIVE_DIV, None))
        return self.backchannel.get()

    def exercise_javascript_bridge(self):
        self.queue.put((CMD_EXERCISE_JAVASCRIPT_BRIDGE, None))
        self.backchannel.get()

    def shutdown(self):
        self.invoice_request_queue.put(CMD_SHUTDOWN)
        self.queue.put((CMD_SHUTDOWN, None))

class InvoiceRequestListener(threading.Thread):
    def __init__(self, queue, invoice_request_callback):
        self.queue = queue
        self.invoice_request_callback = invoice_request_callback
        super(InvoiceRequestListener, self).__init__()

    def run(self):
        is_running = True
        while is_running:
            cmd = self.queue.get()
            if cmd == CMD_CALLBACK:
                self.invoice_request_callback()
            elif cmd == CMD_SHUTDOWN:
                is_running = False


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
            elif cmd == CMD_SHOW_IDLE:
                self.frontend_process.show_idle()
                self.backchannel.put(None)
            elif cmd == CMD_SHOW_PAID:
                self.frontend_process.show_paid()
                self.backchannel.put(None)
            elif cmd == CMD_GET_ACTIVE_DIV:
                answer = self.frontend_process.get_active_div()
                self.backchannel.put(answer)
            elif cmd == CMD_EXERCISE_JAVASCRIPT_BRIDGE:
                self.frontend_process.exercise_javascript_bridge()
                self.backchannel.put(None)
            elif cmd == CMD_SHUTDOWN:
                self.frontend_process.shutdown()
                is_running = False

class FrontendProcess(Process):
    def __init__(self, frontend_type, queue, backchannel,
            invoice_request_queue):
        self.frontend_type = frontend_type
        self.queue = queue
        self.backchannel = backchannel
        self.invoice_request_queue = invoice_request_queue
        super(FrontendProcess, self).__init__()

    def run(self):
        self.app = QtGui.QApplication([])

        ready_for_cmds = threading.Event()
        self.display = Display(FRONTEND_HTML, ready_for_cmds,
                self.invoice_request_queue)
        if (self.frontend_type == Frontend.TYPE_FRONTEND_SMALL_DISPLAY):
            self.display.resize(320, 240)
        if (self.frontend_type == Frontend.TYPE_FRONTEND_FULLSCREEN):
            self.display.showFullScreen()
        if (self.frontend_type != Frontend.TYPE_FRONTEND_INVISIBLE):
            self.display.show()

        self.app.connect(self.app,
                QtCore.SIGNAL('_show_invoice(PyQt_PyObject)'),
                self._show_invoice)
        self.app.connect(self.app,
                QtCore.SIGNAL('_show_idle()'),
                self._show_idle)
        self.app.connect(self.app,
                QtCore.SIGNAL('_show_paid()'),
                self._show_paid)
        self.app.connect(self.app,
                QtCore.SIGNAL('_get_active_div(PyQt_PyObject)'),
                self._get_active_div)
        self.app.connect(self.app,
                QtCore.SIGNAL('_exercise_javascript_bridge()'),
                self._exercise_javascript_bridge)
        self.app.connect(self.app,
                QtCore.SIGNAL('_shutdown()'),
                self._shutdown)

        # init complete; start listening for commands when the page is ready
        self.cmd_listener = CmdListener(self, self.queue, self.backchannel,
                ready_for_cmds)
        self.cmd_listener.start()

        self.app.exec_()

    def show_invoice(self, bitcoin_uri):
        self.app.emit(QtCore.SIGNAL('_show_invoice(PyQt_PyObject)'),
                bitcoin_uri)

    def _show_invoice(self, bitcoin_uri):
        self.display.show_invoice(bitcoin_uri)

    def show_idle(self):
        self.app.emit(QtCore.SIGNAL('_show_idle()'))

    def _show_idle(self):
        self.display.show_idle()

    def show_paid(self):
        self.app.emit(QtCore.SIGNAL('_show_paid()'))

    def _show_paid(self):
        self.display.show_paid()

    def get_active_div(self):
        answer_queue = Queue()
        self.app.emit(QtCore.SIGNAL('_get_active_div(PyQt_PyObject)'), answer_queue)
        return answer_queue.get()

    def _get_active_div(self, answer_queue):
        answer = self.display.get_active_div()
        answer_queue.put(answer)

    def exercise_javascript_bridge(self):
        self.app.emit(QtCore.SIGNAL('_exercise_javascript_bridge()'))

    def _exercise_javascript_bridge(self):
        self.display.exercise_javascript_bridge()

    def shutdown(self):
        self.app.emit(QtCore.SIGNAL('_shutdown()'))

    def _shutdown(self):
        QtGui.QApplication.exit()

class Display(QWebView):
    def __init__(self, page, ready_for_cmds, invoice_request_queue):
        QWebView.__init__(self)
        self.setWindowTitle(FRONTEND_WINDOW_TITLE)
        self.ready_for_cmds = ready_for_cmds
        self.page().loadFinished.connect(self.page_is_ready)
        self.page().mainFrame().addToJavaScriptWindowObject("pyObj",
                JavascriptBridge(invoice_request_queue))
        self.load(QtCore.QUrl(page))

    def page_is_ready(self):
        self.ready_for_cmds.set()

    def show_invoice(self, bitcoin_uri):
        (_, size, img) = qrencode.encode_scaled(bitcoin_uri, QR_CODE_SIZE)
        buf = StringIO()
        img.save(buf, format='PNG')
        image_data = "data:image/png,%s" % urllib.quote(buf.getvalue())
        self._evaluate_java_script('show_invoice("%s")' % image_data)

    def show_idle(self):
        self._evaluate_java_script('show_idle()')

    def show_paid(self):
        self._evaluate_java_script('show_paid()')

    def get_active_div(self):
        return self._evaluate_java_script('get_active_div()').toString()

    def exercise_javascript_bridge(self):
        self._evaluate_java_script('exercise_javascript_bridge()')

    def _evaluate_java_script(self, js):
        return self.page().mainFrame().evaluateJavaScript(js)

    def closeEvent(self, event):
        event.accept()
        QtGui.QApplication.exit()

class JavascriptBridge(QtCore.QObject):
    def __init__(self, invoice_request_queue):
        self.invoice_request_queue = invoice_request_queue
        super(JavascriptBridge, self).__init__()

    @QtCore.pyqtSlot()
    def request_new_invoice(self):
        self.invoice_request_queue.put(CMD_CALLBACK)

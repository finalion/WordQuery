# Copyright: Damien Elmes <anki@ichi2.net>
# -*- coding: utf-8 -*-
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import time
from collections import defaultdict
from aqt.qt import *
from .lang import _
# fixme: if mw->subwindow opens a progress dialog with mw as the parent, mw
# gets raised on finish on compiz. perhaps we should be using the progress
# dialog as the parent?

# Progress info
##########################################################################


class ProgressManager(object):

    def __init__(self, mw):
        self.mw = mw
        self.app = QApplication.instance()
        self.blockUpdates = False
        self._win = None
        self._levels = 0
        self.aborted = False
        self.rows_number = 0
        self._msg_info = defaultdict(dict)
        self._msg_count = defaultdict(int)
    # Creating progress dialogs
    ##########################################################################

    @pyqtSlot(dict)
    def update_labels(self, data):
        if data.type == 'count':
            self._msg_count.update(data)
        else:
            self._msg_info[data.index] = data

        lst = []
        for index in range(self.rows_number):
            info = self._msg_info.get(index, None)
            if not info:
                continue
            if info.type == 'text':
                lst.append(info.text)
            else:
                lst.append(u"{2} [{0}] {1}".format(
                    info.service_name, info.field_name, info.flag))

        number_info = ''
        words_number, fields_number = (
            self._msg_count['words_number'],  self._msg_count['fields_number'])
        if words_number or fields_number:
            number_info += '<br>' + 45 * '-' + '<br>'
            number_info += u'{0} {1} {2}, {3} {4}'.format(
                _('QUERIED'), words_number, _(
                    'WORDS'), fields_number, _('FIELDS')
            )

        self.update('<br>'.join(lst) + number_info)
        self._win.adjustSize()

    def update_title(self, title):
        self._win.setWindowTitle(title)

    def update_rows(self, number):
        self.rows_number = number
        self._msg_info.clear()

    def reset_count(self):
        self._msg_count.clear()

    def start(self, max=0, min=0, label=None, parent=None, immediate=False, rows=0):
        self._msg_info.clear()
        self._msg_count.clear()
        self.rows_number = rows
        self.aborted = False
        self._levels += 1
        if self._levels > 1:
            return
        # setup window
        parent = parent or self.app.activeWindow() or self.mw
        label = label or _("Processing...")
        cancel_btn = QPushButton("Cancel")
        self._win = QProgressDialog(label, "", min, max, parent)
        self._win.setWindowTitle("Querying...")
        self._win.setCancelButton(None)
        # cancel_btn.clicked.connect(self.abort)
        # self._win.setAutoClose(False)
        # self._win.setAutoReset(False)
        self._win.setWindowModality(Qt.ApplicationModal)
        # we need to manually manage minimum time to show, as qt gets confused
        # by the db handler
        self._win.setMinimumDuration(100000)
        if immediate:
            self._shown = True
            self._win.show()
            self.app.processEvents()
        else:
            self._shown = False
        self._counter = min
        self._min = min
        self._max = max
        self._firstTime = time.time()
        self._lastUpdate = time.time()
        self._disabled = False

    def update(self, label=None, value=None, process=True, maybeShow=True):
        # print self._min, self._counter, self._max, label, time.time() -
        # self._lastTime
        if maybeShow:
            self._maybeShow()
        elapsed = time.time() - self._lastUpdate
        if label:
            self._win.setLabelText(label)
        if self._max and self._shown:
            self._counter = value or (self._counter + 1)
            self._win.setValue(self._counter)
        if process and elapsed >= 0.2:
            self.app.processEvents(QEventLoop.ExcludeUserInputEvents)
            self._lastUpdate = time.time()

    def abort(self):
        # self.aborted = True
        return self._win.wasCanceled()

    def finish(self):
        self._levels -= 1
        self._levels = max(0, self._levels)
        if self._levels == 0 and self._win:
            self._win.cancel()
            self._unsetBusy()

    def clear(self):
        "Restore the interface after an error."
        if self._levels:
            self._levels = 1
            self.finish()

    def _maybeShow(self):
        if not self._levels:
            return
        if self._shown:
            self.update(maybeShow=False)
            return
        delta = time.time() - self._firstTime
        if delta > 0.5:
            self._shown = True
            self._win.show()
            self._setBusy()

    def _setBusy(self):
        self._disabled = True
        self.mw.app.setOverrideCursor(QCursor(Qt.WaitCursor))

    def _unsetBusy(self):
        self._disabled = False
        self.app.restoreOverrideCursor()

    def busy(self):
        "True if processing."
        return self._levels

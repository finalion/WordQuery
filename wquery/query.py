#-*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import re
import os
import aqt
from aqt import mw
from aqt.qt import QObject, pyqtSignal, pyqtSlot, QThread
from aqt.utils import showInfo,  tooltip
from collections import defaultdict
import wquery.context as c
import sqlite3
from .service import service_manager
from .utils import Queue, Empty
import time


@pyqtSlot(dict)
def update_progress_label(info):
    update_progress_label.kwargs.update(info)
    words_number, fields_number = update_progress_label.kwargs.get(
        'words_number', 0), update_progress_label.kwargs.get('fields_number', 0)
    number_info = '<br>已查询%d个单词, %d个字段' % (
        words_number, fields_number) if words_number and fields_number else ""
    mw.progress.update(label="Querying <b>%s</b>...<br>[%s] %s%s" % (
        update_progress_label.kwargs[
            'word'], update_progress_label.kwargs['service_name'],
        update_progress_label.kwargs['field_name'], number_info))
# update_progress_label.kwargs = defaultdict(str)


def query_from_menu():
    browser = c.context['browser']
    if not browser:
        return
    notes = [browser.mw.col.getNote(note_id)
             for note_id in browser.selectedNotes()]
    if len(notes) == 0:
        return
    if len(notes) == 1:
        c.context['editor'] = browser.editor

        query_from_editor()
    if len(notes) > 1:
        fields_number = 0
        update_progress_label.kwargs = defaultdict(str)
        mw.progress.start(immediate=True, label="Querying...")
        for i, note in enumerate(notes):
            word = note.fields[0]
            c.maps = c.mappings[note.model()['id']]
            results = query_all_flds(word)
            for j, res in results.items():
                if res == "":
                    if c.update_all:
                        note.fields[j] = res
                else:
                    note.fields[j] = res
                note.flush()
            fields_number += len(results)
            update_progress_label(
                {'words_number': i + 1, 'fields_number': fields_number})
        browser.model.reset()
        mw.progress.finish()
        # browser.model.reset()
        # browser.endReset()
        tooltip(u'共更新 %d 张卡片' % len(notes))


def purify_word(word):
    m = re.search('\s*[a-zA-Z]+[a-zA-Z -]*', word)
    if m:
        return m.group().strip()
    return ""


def query_from_editor():
    editor = c.context['editor']
    if not editor:
        return
    word = editor.note.fields[0].decode('utf-8')
    c.maps = c.mappings[editor.note.model()['id']]
    mw.progress.start(immediate=True, label="Querying <b>%s<b>..." % word)
    update_progress_label.kwargs = defaultdict(str)
    results = query_all_flds(word)
    for i, res in results.items():
        if res == "":
            if c.update_all:
                editor.note.fields[i] = res
        else:
            editor.note.fields[i] = res
    update_progress_label(
        {'words_number': 1, 'fields_number': len(results)})
    # editor.note.flush()
    mw.progress.finish()
    editor.setNote(editor.note, focus=True)
    editor.saveNow()


def query_all_flds(word):
    handle_results.total = dict()
    purified_word = purify_word(word)
    for i, each in enumerate(c.maps):
        use_dict = each.get('checked', False)
        dict_type = each.get('dict', '').strip()
        dict_field = each.get('dict_field', '').strip()
        res = ""
        if i == 0:
            res = word
        else:
            if use_dict and dict_type and dict_field:
                worker = work_manager.get_worker(dict_type)
                worker.target(i, dict_field, purified_word)
                worker.start()
    for name, worker in work_manager.workers.items():
        while not worker.isFinished():
            mw.app.processEvents()
            worker.wait(100)

    return handle_results('__query_over__')


@pyqtSlot(dict)
def handle_results(result):
    # showInfo('slot: ' + str(result))
    if result != '__query_over__':
        handle_results.total.update(result)
    return handle_results.total


class QueryWorkerManager(object):

    def __init__(self):
        self.workers = defaultdict(QueryWorker)

    def get_worker(self, service_name):
        if service_name not in self.workers:
            worker = QueryWorker(service_name)
            self.workers[service_name] = worker
        else:
            worker = self.workers[service_name]
        return worker


class QueryWorker(QThread):

    result_ready = pyqtSignal(dict)
    progress_update = pyqtSignal(dict)

    def __init__(self, service_name):
        super(QueryWorker, self).__init__()
        self.service_name = service_name
        self.queue = Queue()
        self.service = service_manager.get_service(service_name)
        self.result_ready.connect(handle_results)
        self.progress_update.connect(update_progress_label)

    def target(self, index, service_field, word):
        self.queue.put((index, service_field, word))

    def run(self):
        # try:
        while True:
            try:
                index, service_field, word = self.queue.get(timeout=0.1)
                field_info = os.path.basename(service_field) if os.path.isabs(
                    service_field) else service_field
                self.progress_update.emit(
                    {'service_name': self.service_name, 'word': word, 'service_field': service_field, 'field_name': field_info})
                # name = self.service.instance.__class__.__name__
                result = self.query(
                    service_field, word) if self.service else ""
                self.result_ready.emit({index: result})
                # time.sleep(1)
                # showInfo("%d:  %s" % (index, result))
            except Empty:
                break

    def query(self, service_field, word):

        return self.service.instance.active(service_field, word)

work_manager = QueryWorkerManager()

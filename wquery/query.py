#-*- coding:utf-8 -*-
import os
import re
import sqlite3
import sys
import time
from collections import defaultdict

import aqt
from aqt import mw
from aqt.qt import QObject, QThread, pyqtSignal, pyqtSlot
from aqt.utils import showInfo, showText, tooltip

from .context import config, context
from .lang import _, _sl
from .service import service_manager
from .service.base import QueryResult
from .utils import Empty, Queue
from .progress import ProgressManager

reload(sys)
sys.setdefaultencoding('utf8')


@pyqtSlot(dict)
def update_progress_label(info):
    update_progress_label.kwargs.update(info)
    words_number, fields_number = update_progress_label.kwargs.get(
        'words_number', 0), update_progress_label.kwargs.get('fields_number', 0)
    number_info = '<br>%s %d %s, %d %s' % (_('QUERIED'), words_number,
                                           _('WORDS'), fields_number, _('FIELDS')) \
        if words_number and fields_number else ""
    progress.update(label="Querying <b>%s</b>...<br>[%s] %s%s" % (
        update_progress_label.kwargs['word'],
        update_progress_label.kwargs['service_name'],
        update_progress_label.kwargs['field_name'], number_info))


def inspect_note(note):
    '''
    inspect the note, and get necessary input parameters
    return word_ord: field index of the word in current note
    return word: the word
    return maps: dicts map of current note
    '''
    maps = config.get_maps(note.model()['id'])
    for i, m in enumerate(maps):
        if m.get('word_checked', False):
            word_ord = i
            break
    else:
        # if no field is checked to be the word field, default the
        # first one.
        word_ord = 0

    def purify_word(word):
        return word.lower().strip() if word else ''

    word = purify_word(note.fields[word_ord].decode('utf-8'))
    return word_ord, word, maps


def query_from_browser():
    work_manager.reset_query_counts()
    browser = context['browser']
    if not browser:
        return
    notes = [browser.mw.col.getNote(note_id)
             for note_id in browser.selectedNotes()]
    if len(notes) == 0:
        return
    if len(notes) == 1:
        context['editor'] = browser.editor
        query_from_editor()
    if len(notes) > 1:
        fields_number = 0
        update_progress_label.kwargs = defaultdict(str)
        progress.start(immediate=True, label="Querying...")
        for i, note in enumerate(notes):
            # user cancels the progress
            if progress.abort():
                break
            word_ord, word, maps = inspect_note(note)
            if not word:
                continue
            results = query_all_flds(word_ord, word, maps)
            for j, q in results.items():
                update_note_field(note, j, q)
                # note.flush()
            fields_number += len(results)
            update_progress_label(
                {'words_number': i + 1, 'fields_number': fields_number})
        browser.model.reset()
        progress.finish()
        # browser.model.reset()
        # browser.endReset()
        tooltip(u'%s %d %s' % (_('UPDATED'),
                               work_manager.completed_query_counts(),
                               _('CARDS')))


def query_from_editor():
    work_manager.reset_query_counts()
    editor = context['editor']
    if not editor:
        return
    word, word_ord = None, 0
    fld_index = editor.currentField
    word_ord, word, maps = inspect_note(editor.note)
    if not word:
        showInfo(_("NO_QUERY_WORD"))
        return
    progress.start(immediate=True, label="Querying...")
    update_progress_label.kwargs = defaultdict(str)
    # if the focus falls into the word field, then query all note fields,
    # else only query the current focused field.
    if fld_index == word_ord:
        results = query_all_flds(word_ord, word, maps)
    else:
        results = query_single_fld(word, fld_index, maps)
    for i, q in results.items():
        update_note_field(editor.note, i, q)
    # editor.note.flush()
    # showText(str(editor.note.model()['tmpls']))
    progress.finish()
    editor.setNote(editor.note, focus=True)
    editor.saveNow()


def update_note_field(note, fld_index, content):
    if not isinstance(content, QueryResult):
        return
    content, js, css = content.result, content.js, content.css
    # js process: add to template of the note model
    if js:
        add_to_tmpl(note, js=js)
    # css process: add css directly to the note field, that can ensure there
    # will not exist css confusion
    if css:
        content = css + content
    note.fields[fld_index] = content
    note.flush()


def add_to_tmpl(note, **kwargs):
    # templates
    '''
    [{u'name': u'Card 1', u'qfmt': u'{{Front}}\n\n', u'did': None, u'bafmt': u'',
        u'afmt': u'{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}\n\n{{12}}\n\n{{44}}\n\n', u'ord': 0, u'bqfmt': u''}]
    '''
    # showInfo(str(kwargs))
    afmt = note.model()['tmpls'][0]['afmt']
    if kwargs:
        for key, value in kwargs.items():
            value = value.strip()
            if key == 'js' and value not in afmt:
                js = value
                if not value.startswith('<script') and not value.endswith('/script>'):
                    js = '<script>%s</script>' % value
                note.model()['tmpls'][0]['afmt'] = afmt + js


def query_single_fld(word, fld_index, maps):
    # assert fld_index > 0
    if fld_index >= len(maps):
        return QueryResult()
    handle_results.total = defaultdict(QueryResult)
    dict_name = maps[fld_index].get('dict', '').strip()
    dict_field = maps[fld_index].get('dict_field', '').strip()
    dict_unique = maps[fld_index].get('dict_unique', '').strip()
    # update_progress_label(
    #     {'word': word, 'service_name': dict_name, 'field_name': dict_field})
    if dict_name and dict_name not in _sl('NOT_DICT_FIELD') and dict_field:
        worker = work_manager.get_worker(dict_unique)
        worker.target(fld_index, dict_field, word)
    work_manager.start_all_workers()
    return join_result()


def query_all_flds(word_ord, word, maps):
    handle_results.total = defaultdict(QueryResult)
    for i, each in enumerate(maps):
        if i == word_ord:
            continue
        dict_name = each.get('dict', '').strip()
        dict_field = each.get('dict_field', '').strip()
        dict_unique = each.get('dict_unique', '').strip()
        # webservice manager 使用combobox的文本值选择服务
        # mdxservice manager 使用combox的itemData即字典路径选择服务
        if dict_name and dict_name not in _sl('NOT_DICT_FIELD') and dict_field:
            worker = work_manager.get_worker(dict_unique)
            worker.target(i, dict_field, word)
    work_manager.start_all_workers()
    return join_result()


def join_result():
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

    def get_worker(self, service_unique):
        if service_unique not in self.workers:
            worker = QueryWorker(service_unique)
            self.workers[service_unique] = worker
        else:
            worker = self.workers[service_unique]
        return worker

    def start_all_workers(self):
        for worker in self.workers.values():
            worker.start()

    def reset_query_counts(self):
        for worker in self.workers.values():
            worker.completed_counts = 0

    def completed_query_counts(self):
        return sum([worker.completed_counts for worker in self.workers.values()])


class QueryWorker(QThread):

    result_ready = pyqtSignal(dict)
    progress_update = pyqtSignal(dict)

    def __init__(self, service_unique):
        super(QueryWorker, self).__init__()
        self.service_unique = service_unique
        self.service = service_manager.get_service(service_unique)
        self.completed_counts = 0
        self.queue = Queue()
        self.result_ready.connect(handle_results)
        self.progress_update.connect(update_progress_label)

    def target(self, index, service_field, word):
        self.queue.put((index, service_field, word))

    def run(self):
        # self.completed_counts = 0
        while True:
            try:
                index, service_field, word = self.queue.get(timeout=0.1)
                self.progress_update.emit({
                    'service_name': self.service.title,
                    'word': word,
                    'field_name': service_field
                })
                result = self.query(service_field, word)
                self.result_ready.emit({index: result})
                self.completed_counts += 1
                # rest a moment
                self.rest()
            except Empty:
                break

    def rest(self):
        time.sleep(self.service.query_interval)

    def query(self, service_field, word):
        return self.service.active(service_field, word)


progress = ProgressManager(mw)

work_manager = QueryWorkerManager()

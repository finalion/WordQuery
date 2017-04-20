#-*- coding:utf-8 -*-
#
# Copyright © 2016–2017 Liang Feng <finalion@gmail.com>
#
# Support: Report an issue at https://github.com/finalion/WordQuery/issues
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version; http://www.gnu.org/copyleft/gpl.html.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

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
        query_from_editor_all_fields()
    if len(notes) > 1:
        fields_number = 0
        update_progress_label.kwargs = defaultdict(str)
        progress.start(immediate=True, label="Querying...")
        for i, note in enumerate(notes):
            # user cancels the progress
            if progress.abort():
                break
            try:
                results = query_all_flds(note)
                update_note_fields(note, results)
                fields_number += len(results)
                update_progress_label(
                    {'words_number': i + 1, 'fields_number': fields_number})
            except InvalidWordException:
                showInfo(_("NO_QUERY_WORD"))
        browser.model.reset()
        progress.finish()
        # browser.model.reset()
        # browser.endReset()
        tooltip(u'%s %d %s, %d %s' % (_('UPDATED'),
                                      i + 1,
                                      _('CARDS'),
                                      work_manager.completed_query_counts(),
                                      _('FIELDS')))


def query_from_editor_all_fields():
    work_manager.reset_query_counts()
    editor = context['editor']
    if not editor:
        return
    update_progress_label.kwargs = defaultdict(str)
    progress.start(immediate=True, label="Querying...")
    try:
        results = query_all_flds(editor.note)
        update_note_fields(editor.note, results)
    except InvalidWordException:
        showInfo(_("NO_QUERY_WORD"))
    progress.finish()
    editor.setNote(editor.note, focus=True)
    editor.saveNow()


def query_from_editor_current_field():
    work_manager.reset_query_counts()
    editor = context['editor']
    if not editor:
        return
    update_progress_label.kwargs = defaultdict(str)
    progress.start(immediate=True, label="Querying...")
    # if the focus falls into the word field, then query all note fields,
    # else only query the current focused field.
    fld_index = editor.currentField
    word_ord = inspect_note(editor.note)[0]
    try:
        if fld_index == word_ord:
            results = query_all_flds(editor.note)
        else:
            results = query_single_fld(editor.note, fld_index)
        update_note_fields(editor.note, results)
    except InvalidWordException:
        showInfo(_("NO_QUERY_WORD"))
    # editor.note.flush()
    # showText(str(editor.note.model()['tmpls']))
    progress.finish()
    editor.setNote(editor.note, focus=True)
    editor.saveNow()


def update_note_fields(note, results):
    for i, q in results.items():
        if isinstance(q, QueryResult):
            update_note_field(note, i, q)


def update_note_field(note, fld_index, fld_result):
    result, js, css = fld_result.result, fld_result.js, fld_result.css
    # js process: add to template of the note model
    if js:
        add_to_tmpl(note, js=js)
    # css process: add css directly to the note field, that can ensure there
    # will not exist css confusion
    if css:
        result = css + result
    note.fields[fld_index] = result
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


class InvalidWordException(Exception):
    """Invalid word exception"""


def join_result(query_func):
    def wrap(*args, **kwargs):
        query_func(*args, **kwargs)
        for name, worker in work_manager.workers.items():
            while not worker.isFinished():
                mw.app.processEvents()
                worker.wait(100)
        return handle_results('__query_over__')
    return wrap


@join_result
def query_all_flds(note):
    handle_results.total = defaultdict(QueryResult)
    word_ord, word, maps = inspect_note(note)
    if not word:
        raise InvalidWordException
    for i, each in enumerate(maps):
        if i == word_ord:
            continue
        dict_name = each.get('dict', '').strip()
        dict_field = each.get('dict_field', '').strip()
        dict_unique = each.get('dict_unique', '').strip()
        if dict_name and dict_name not in _sl('NOT_DICT_FIELD') and dict_field:
            worker = work_manager.get_worker(dict_unique)
            worker.target(i, dict_field, word)
    work_manager.start_all_workers()


@join_result
def query_single_fld(note, fld_index):
    handle_results.total = defaultdict(QueryResult)
    word_ord, word, maps = inspect_note(note)
    if not word:
        raise InvalidWordException
    # assert fld_index > 0
    if fld_index >= len(maps):
        return QueryResult()
    dict_name = maps[fld_index].get('dict', '').strip()
    dict_field = maps[fld_index].get('dict_field', '').strip()
    dict_unique = maps[fld_index].get('dict_unique', '').strip()
    # update_progress_label(
    #     {'word': word, 'service_name': dict_name, 'field_name': dict_field})
    if dict_name and dict_name not in _sl('NOT_DICT_FIELD') and dict_field:
        worker = work_manager.get_worker(dict_unique)
        worker.target(fld_index, dict_field, word)
    work_manager.start_all_workers()


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

    def start_worker(self, worker):
        worker.start()

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

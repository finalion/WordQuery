#-*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import re
import os
import time
import sqlite3
from collections import defaultdict
import aqt
from aqt import mw
from aqt.qt import QObject, pyqtSignal, pyqtSlot, QThread
from aqt.utils import showInfo,  tooltip, showText
from .context import context, config
from .service import web_service_manager, mdx_service_manager
from .utils import Queue, Empty
from .service.base import QueryResult
from lang import _


@pyqtSlot(dict)
def update_progress_label(info):
    update_progress_label.kwargs.update(info)
    words_number, fields_number = update_progress_label.kwargs.get(
        'words_number', 0), update_progress_label.kwargs.get('fields_number', 0)
    number_info = '<br>%s %d %s, %d %s' % (_('QUERIED'), words_number, _(
        'WORDS'), fields_number, _('FIELDS')) if words_number and fields_number else ""
    mw.progress.update(label="Querying <b>%s</b>...<br>[%s] %s%s" % (
        update_progress_label.kwargs[
            'word'], update_progress_label.kwargs['service_name'],
        update_progress_label.kwargs['field_name'], number_info))
# update_progress_label.kwargs = defaultdict(str)


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
        # m = re.search('\s*[a-zA-Z]+[a-zA-Z -]*', word)
        # if m:
        #     return m.group().strip()
        # return ""

    word = purify_word(note.fields[word_ord].decode('utf-8'))
    return word_ord, word, maps


def query_from_menu():
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
        mw.progress.start(immediate=True, label="Querying...")
        for i, note in enumerate(notes):
            word_ord, word, maps = inspect_note(note)
            if not word:
                continue
            results = query_all_flds(word_ord, word, maps)
            for j, q in results.items():
                if not isinstance(q, QueryResult):
                    continue
                update_note_field(note, j, q)
                # note.flush()
            fields_number += len(results)
            update_progress_label(
                {'words_number': i + 1, 'fields_number': fields_number})
        browser.model.reset()
        mw.progress.finish()
        # browser.model.reset()
        # browser.endReset()
        tooltip(u'%s %d %s' % (_('UPDATED'), len(notes), _('CARDS')))


def update_note_field(note, fld_index, content):
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


def query_from_editor():
    editor = context['editor']
    if not editor:
        return
    word, word_ord = None, 0
    fld_index = editor.currentField
    word_ord, word, maps = inspect_note(editor.note)
    if not word:
        showInfo(_("NO_QUERY_WORD"))
        return
    mw.progress.start(immediate=True, label="Querying...")
    update_progress_label.kwargs = defaultdict(str)
    # if the focus falls into the word field, then query all note fields,
    # else only query the current focused field.
    if fld_index == word_ord:
        results = query_all_flds(word_ord, word, maps)
        # showText(str(results))
        for i, q in results.items():
            if not isinstance(q, QueryResult):
                continue
            update_note_field(editor.note, i, q)
    else:
        q = query_single_fld(word, fld_index, maps)
        if isinstance(q, QueryResult):
            update_note_field(editor.note, fld_index, q)

    # editor.note.flush()
    # showText(str(editor.note.model()['tmpls']))
    mw.progress.finish()
    editor.setNote(editor.note, focus=True)
    editor.saveNow()


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
    dict_type = maps[fld_index].get('dict', '').strip()
    dict_field = maps[fld_index].get('dict_field', '').strip()
    dict_path = maps[fld_index].get('dict_path', '').strip()
    update_progress_label(
        {'word': word, 'service_name': dict_type, 'field_name': dict_field})
    if dict_type and dict_type != u'不是字典字段' and dict_type != 'Not dict field' and dict_field:
        if dict_path == 'webservice':
            service = web_service_manager.get_service(dict_type)
        if os.path.isabs(dict_path):
            service = mdx_service_manager.get_service(dict_path)
        return service.instance.active(dict_field, word)


def query_all_flds(word_ord, word, maps):
    handle_results.total = defaultdict(QueryResult)
    for i, each in enumerate(maps):
        if i == word_ord:
            continue
        dict_type = each.get('dict', '').strip()
        dict_field = each.get('dict_field', '').strip()
        dict_path = each.get('dict_path', '').strip()
        # webservice manager 使用combobox的文本值选择服务
        # mdxservice manager 使用combox的itemData即字典路径选择服务
        if dict_type and dict_type != u'不是字典字段' and dict_type != 'Not dict field' and dict_field:
            if dict_path == 'webservice':
                worker = work_manager.get_worker(dict_type, 'web')
            if os.path.isabs(dict_path):
                worker = work_manager.get_worker(dict_path, 'mdx')
            worker.target(i, dict_field, word)
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

    def get_worker(self, service_name, type):
        if service_name not in self.workers:
            worker = QueryWorker(service_name, type)
            self.workers[service_name] = worker
        else:
            worker = self.workers[service_name]
        return worker


class QueryWorker(QThread):

    result_ready = pyqtSignal(dict)
    progress_update = pyqtSignal(dict)

    def __init__(self, service_name, type):
        super(QueryWorker, self).__init__()
        self.service_name = service_name
        self.queue = Queue()
        if type == 'web':
            self.service = web_service_manager.get_service(service_name)
        if type == 'mdx':
            self.service = mdx_service_manager.get_service(service_name)
        self.result_ready.connect(handle_results)
        self.progress_update.connect(update_progress_label)

    def target(self, index, service_field, word):
        self.queue.put((index, service_field, word))

    def run(self):
        # try:
        while True:
            try:
                index, service_field, word = self.queue.get(timeout=0.1)
                name_info = os.path.basename(self.service_name) if os.path.isabs(
                    self.service_name) else self.service_name
                self.progress_update.emit(
                    {'service_name': name_info, 'word': word, 'field_name': service_field})
                result = self.query(
                    service_field, word) if self.service else ""
                # showInfo('%d, %s' % (index, str(result)))
                self.result_ready.emit({index: result})
            except Empty:
                break

    def query(self, service_field, word):
        return self.service.instance.active(service_field, word)

work_manager = QueryWorkerManager()

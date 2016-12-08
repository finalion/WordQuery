#-*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import os
import urlparse
import re
import json
import xml
import urllib
import urllib2
import aqt
from aqt import mw
from aqt.qt import *
from aqt.utils import shortcut, showInfo, showText, tooltip
# import trackback
from mdict.mdict_query import IndexBuilder
from collections import defaultdict
import wquery.context as c
import sqlite3
from .service import service_manager


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
        mw.progress.start(immediate=True, label="Querying...")
        for i, note in enumerate(notes):
            word = note.fields[0]
            c.model_id = note.model()['id']
            c.maps = c.mappings[c.model_id]
            for j, res in query_all_flds(word):
                if res == "":
                    if c.update_all:
                        note.fields[j] = res
                else:
                    note.fields[j] = res
                note.flush()
            mw.progress.update(label="Queried %d words..." % (i + 1))
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
    c.model_id = editor.note.model()['id']
    word = editor.note.fields[0].decode('utf-8')
    c.maps = c.mappings[c.model_id]
    mw.progress.start(immediate=True, label="Querying...")
    for i, res in query_all_flds(word):
        if res == "":
            if c.update_all:
                editor.note.fields[i] = res
        else:
            editor.note.fields[i] = res
    # editor.note.flush()
    mw.progress.finish()
    editor.setNote(editor.note, focus=True)
    editor.saveNow()


def query_all_flds(word):
    purified_word = purify_word(word)
    for i, each in enumerate(c.maps):
        res = ""
        if i == 0:
            res = word
        else:
            if each['checked'] and each['dict'].strip():
                res = query_mdict(purified_word, i, **each)
        yield i, res


def query_mdict(word, ix, **kwargs):
    dict_path = kwargs.get('dict', '').strip()
    dict_field = kwargs.get('dict_field', '').strip()
    if dict_field.startswith("http://"):
        service = service_manager.get_service(dict_path)
        if service:
            result = service.instance.active(dict_field, word)
            return result

    elif os.path.isabs(dict_field):
        service = service_manager.get_service(dict_path)
        if service:
            result = service.instance.active(dict_field, word)
            return result
    else:
        service = service_manager.get_service(dict_path)
        if service:
            # showInfo(word)
            result = service.instance.active(dict_field, word)
            return result

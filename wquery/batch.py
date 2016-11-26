#-*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import os
import re
import aqt
from aqt import mw
from aqt.qt import *
from aqt.studydeck import StudyDeck
from aqt.utils import shortcut, showInfo, showText, tooltip, showWarning, getFile
from anki.importing import TextImporter
# import trackback
from collections import defaultdict
from wquery.query import index_mdx
from wquery.query import query_mdict
import wquery.context as c


class BatchImporter(TextImporter):

    def initMapping(self):
        flds = [f['name'] for f in self.model['flds']]
        # truncate to provided count
        # flds = flds[0:self.fields()]
        # if there's room left, add tags
        if self.fields() > len(flds):
            flds.append("_tags")
        # and if there's still room left, pad
        flds = flds + [None] * (self.fields() - len(flds))
        self.mapping = flds


def register_importer():
    pass


def batch_import():
    file = getFile(mw, _("Import"), None, key="import",
                   filter="Text separated by tabs or semicolons (*)")
    if not file:
        return
    file = str(file)
    importFile(mw, file)


def importFile(mw, file):
    importer = BatchImporter(mw.col, file)
    # make sure we can load the file first
    showInfo("batch importer")
    mw.progress.start(immediate=True)
    try:
        importer.open()
    except UnicodeDecodeError:
        showWarning(_(
            "Selected file was not in UTF-8 format. Please see the "
            "importing section of the manual."))
        return
    except Exception as e:
        msg = repr(str(e))
        showWarning(msg)
        return
    finally:
        mw.progress.finish()
    diag = aqt.importing.ImportDialog(mw, importer)
    mw.reset()


def select():
    # select deck. Reuse deck if already exists, else add a desk with
    # deck_name.
    widget = QWidget()
    # prompt dialog to choose deck
    ret = StudyDeck(
        mw, current=None, accept=_("Choose"),
        title=_("Choose Deck"), help="addingnotes",
        cancel=False, parent=widget, geomKey="selectDeck")
    did = mw.col.decks.id(ret.name)
    mw.col.decks.select(did)
    if not ret.name:
        return None, None
    deck = mw.col.decks.byName(ret.name)

    def nameFunc():
        return sorted(mw.col.models.allNames())
    ret = StudyDeck(
        mw, names=nameFunc, accept=_("Choose"), title=_("Choose Note Type"),
        help="_notes", parent=widget,
        cancel=True, geomKey="selectModel")
    if not ret.name:
        return None, None
    model = mw.col.models.byName(ret.name)
    # deck['mid'] = model['id']
    # mw.col.decks.save(deck)
    return model, deck


class BatchQueryer(QThread):

    def __init__(self, filepath, queue):
        QThread.__init__(self)
        self.filepath = filepath
        self.queue = queue

    def run(self):
        with open(self.filepath, 'rb') as f:
            for line in f:  # 每行一个单词
                l = [each.strip() for each in line.split('\t')]
                word, sentence = l if len(l) == 2 else (l[0], "")
                if word:
                    d = defaultdict(str)
                    m = re.search('\((.*?)\)', word)
                    if m:
                        word = m.groups()[0]
                    # 单词解析完毕
                    for i, each in enumerate(c.maps):
                        # 根据设置好的字段和字典的映射关系，轮询取每个字典的释义
                        if each['checked'] and each['dict_path'].strip():
                            d[i] = query_mdict(word, i, **each)
                    self.queue.append((word, d))


def batch_import2():
    """
    Use addNote method to add the note one by one, but it can't check if the card exists now.
    """
    filepath = QFileDialog.getOpenFileName(
        caption="select words table file", directory=os.path.dirname(""), filter="All Files(*.*)")
    if not filepath:
        return
    model, deck = select()
    if not model:
        return
    if mw.col.conf.get("addToCur", True):
        did = mw.col.conf['curDeck']
        if mw.col.decks.isDyn(did):
            did = 1
    else:
        did = model['did']

    if did != model['did']:
        model['did'] = did
        mw.col.models.save(model)
    mw.col.decks.select(did)
    index_mdx()
    queue = list()
    # query
    query_thread = BatchQueryer(filepath, queue)
    query_thread.start()
    mw.progress.start(immediate=True, label="Batch Querying and Adding...")
    while not query_thread.isFinished():
        mw.app.processEvents()
        query_thread.wait(100)
    mw.progress.finish()

    # insert
    numbers = 0
    for word, data in queue:
        note = mw.col.newNote()
        for ix, each in enumerate(c.maps):
            fld_name = c.maps[ix]['fld_name']
            if ix == 0:
                note[fld_name] = word.decode('utf-8')
            else:
                note[fld_name] = data[ix].decode('utf-8')
        numbers += mw.col.addNote(note)
    tooltip(u'共批量导入%d张笔记' % numbers)
    mw.reset()

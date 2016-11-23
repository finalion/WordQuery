#-*- coding:utf-8 -*-

import sys

reload(sys)
sys.setdefaultencoding('utf8')

import os
import re
import urllib2
import xml.etree.ElementTree
from StringIO import StringIO
import json
import aqt
from aqt import mw
from aqt.qt import *
from anki.hooks import addHook, runHook, wrap
from anki.importing import TextImporter
from aqt.addcards import AddCards
from aqt.modelchooser import ModelChooser
from aqt.studydeck import StudyDeck
from aqt.toolbar import Toolbar
from aqt.utils import shortcut, showInfo
# import trackback
from mdict.mdict_query import IndexBuilder
import cPickle
# from Queue import Queue
from collections import defaultdict


enable_youdao = 0

default_server = 'http://127.0.0.1:8000'
index_builders = defaultdict(int)
dictpath = ''
savepath = os.path.join(sys.path[0], 'config')
# showInfo(','.join(sys.path))

serveraddr = default_server
use_local, use_server = False, False

rules = list()
with open(os.path.join(sys.path[0], 'rules.json'), 'rb') as f:
    rules = json.load(f)["fields"]


def find_rule(**kwargs):
    for rule in rules:
        # print rule.items(), kwargs.items()
        for arg in kwargs.items():
            if arg in rule.items():
                return rule


def read_parameters():
    try:
        with open(savepath, 'rb') as f:
            return cPickle.load(f)
        # showInfo(str(paras))
    except:
        # showInfo("config file error")
        return None


def set_parameters():
    global paras
    cbs, les, lbs = mw.myWidget.findChildren(
        QCheckBox), mw.myWidget.findChildren(QLineEdit), mw.myWidget.findChildren(QLabel)
    paras = [{"checked": cb.isChecked(), "dict_path": le.text().strip(), "fld_name": lb.text()}
             for (cb, le, lb) in zip(cbs, les, lbs)]
    # showInfo(str(paras))
    with open(savepath, 'wb') as f:
        cPickle.dump(paras, f)


class MdxIndexer(QThread):

    def __init__(self, ix):
        QThread.__init__(self)
        self.ix = ix

    def run(self):
        if self.ix == -1:
            for i, each in enumerate(paras):
                if each['checked'] and each["dict_path"]:
                    index_builders[i] = self.work(each["dict_path"])
        else:
            index_builders[self.ix] = self.work(paras[self.ix]["dict_path"])

    def work(self, dict_path):
        index_builder = IndexBuilder(dict_path)
        errors = save_media_files(index_builder, '*.css', '.js')
        if '*.css' in errors:
        # info = ' '.join([each[2:] for each in ['*.css', '*.js'] if each in errors ])
            showInfo(u"%s字典中缺失css文件，格式显示可能不正确，请自行查找文件并放入媒体文件夹中"%(dict_path))
        return index_builder


def index_mdx(ix=-1):
    mw.progress.start(immediate=True, label="Index building...")
    index_thread = MdxIndexer(ix)
    index_thread.start()
    while not index_thread.isFinished():
        mw.app.processEvents()
        index_thread.wait(100)
    mw.progress.finish()


def btn_ok_pressed():
    mw.myWidget.close()
    set_parameters()
    index_mdx(-1)


def btn_models_pressed():
    model = show_models()
    if model:
        build_layout(model)


def select_dict(fld_number):
    path = QFileDialog.getOpenFileName(
        caption="select dictionary", directory="", filter="mdx Files(*.mdx)")
    if path:
        path = unicode(path)
        path_edits = mw.myWidget.findChildren(QLineEdit)
        path_edits[fld_number].setText(path)


def chkbox_state_changed(fld_number):
    dict_checks = mw.myWidget.findChildren(QCheckBox)
    line_edits = mw.myWidget.findChildren(QLineEdit)
    line_edits[fld_number].setReadOnly(
        dict_checks[fld_number].checkState() == 0)


def clear_layout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clear_layout(item.layout())


def build_layout(model=None):
    clear_layout(mw.myDictsLayout)
    if model:
        for i, fld in enumerate(model['flds']):
            add_dict_layout(i, fld_name=fld['name'])
    else:
        # build from config
        for i, each in enumerate(paras):
            add_dict_layout(i, **each)
    mw.myWidget.setLayout(mw.myMainLayout)


def show_models():
    ret = StudyDeck(
        mw, names=lambda: sorted(mw.col.models.allNames()), accept=_("Choose"), title=_("Choose Note Type"),
        help="_notes", parent=mw.myWidget,
        cancel=True, geomKey="selectModel")
    if ret.name:
        model = mw.col.models.byName(ret.name)
        return model


def add_dict_layout(i, **kwargs):
    """
    kwargs:
    checked  dict_path  fld_name 
    """
    checked, dict_path, fld_name = kwargs.get('checked', False), kwargs.get(
        'dict_path', ''), kwargs.get('fld_name', '')
    layout = QHBoxLayout()
    dict_check = QCheckBox(u"使用字典")
    dict_check.setChecked(checked)
    path_edit = QLineEdit(dict_path)
    path_edit.setReadOnly(not checked)
    objname = "fld%d" % i
    path_edit.setObjectName(objname)
    # important! only myWidget can find the children!!!!
    # when use some joined string, it can not find too !!!
    # ss = mw.myWidget.findChildren(QLineEdit, objname)
    # if ss:
    #     showInfo("found %d" % i)
    field_label = QLabel(fld_name)
    choose_btn = QPushButton(u"选择")
    mw.myWidget.connect(choose_btn, SIGNAL("clicked()"),
                        mw.signal_mapper_sel, SLOT("map()"))
    mw.myWidget.connect(dict_check, SIGNAL("clicked()"),
                        mw.signal_mapper_chk, SLOT("map()"))
    mw.signal_mapper_sel.setMapping(choose_btn, i)
    mw.signal_mapper_chk.setMapping(dict_check, i)
    layout.addWidget(dict_check)
    layout.addWidget(field_label)
    layout.addWidget(path_edit)
    layout.addWidget(choose_btn)
    mw.myDictsLayout.addLayout(layout)
    mw.myWidget.setLayout(mw.myMainLayout)


def set_options():
    global paras
    paras = read_parameters()
    mw.myWidget = widget = QWidget()
    mw.myMainLayout = main_layout = QVBoxLayout()
    mw.myDictsLayout = dicts_layout = QVBoxLayout()
    mw.signal_mapper_sel = QSignalMapper(mw.myWidget)
    mw.signal_mapper_chk = QSignalMapper(mw.myWidget)
    models_button = QPushButton("Choose Note Type")
    models_button.clicked.connect(btn_models_pressed)
    # build fields -- dicts layout
    if paras:
        build_layout()
    ok_button = QPushButton("OK")
    ok_button.clicked.connect(btn_ok_pressed)
    main_layout.addWidget(models_button)
    main_layout.addLayout(dicts_layout)
    main_layout.addWidget(ok_button)
    mw.signal_mapper_sel.mapped.connect(select_dict)
    mw.signal_mapper_chk.mapped.connect(chkbox_state_changed)
    widget.setLayout(main_layout)
    widget.show()


def my_setupButtons(self):
    bb = self.form.buttonBox
    ar = QDialogButtonBox.ActionRole
    self.queryButton = bb.addButton(_("Query"), ar)
    self.queryButton.clicked.connect(self.query)
    self.queryButton.setShortcut(QKeySequence("Ctrl+Q"))
    self.queryButton.setToolTip(shortcut(_("Query (shortcut: ctrl+q)")))


def query(self):
    for field in self.editor.note.fields:
        field = ''
    # self.query_youdao()
    for i, each in enumerate(paras):
        self.query_mdict(
            i, **each) if each['checked'] and each['dict_path'].strip() else 0

    self.editor.setNote(self.editor.note, focus=True)


def query_youdao(self):
    note = self.editor.note
    word = note.fields[0]      # choose the first field as the word
    # showInfo('youdoa:%s'%word)
    result = urllib2.urlopen(
        "http://dict.youdao.com/fsearch?client=deskdict&keyfrom=chrome.extension&pos=-1&doctype=xml&xmlVersion=3.2&dogVersion=1.0&vendor=unknown&appVer=3.1.17.4208&le=eng&q=%s" % word, timeout=5).read()
    file = StringIO(result)
    doc = xml.etree.ElementTree.parse(file)
    # fetch symbols
    symbol, uk_symbol, us_symbol = doc.findtext(".//phonetic-symbol"), doc.findtext(
        ".//uk-phonetic-symbol"), doc.findtext(".//us-phonetic-symbol")
    # showInfo(','.join([symbol, uk_symbol, us_symbol]))
    try:
        note.fields[1] = 'UK [%s] US [%s]' % (uk_symbol, us_symbol)
        # fetch explanations
        note.fields[3] = '<br>'.join([node.text for node in doc.findall(
            ".//custom-translation/translation/content")])
    except:
        showInfo("Template Error, online!")


def query_mdict(self, ix, **kwargs):
    note = self.editor.note
    word = note.fields[0]      # choose the first field as the word
    result = None
    dict_path, fld_name = kwargs.get(
        'dict_path', '').strip(), kwargs.get('fld_name', '').strip()
    use_server = dict_path.startswith("http://")
    use_local = not use_server
    if use_local:
        # showInfo("  fill: %d   query: %s " % (ix, dict_path))
        if not index_builders[ix]:
            index_mdx(ix)
        # index_mdx() if not index_builder else 0
        result = index_builders[ix].mdx_lookup(word)
        # showInfo(result[0])
        if result:
            self.update_dict_field(ix, result[0], index_builders[ix])
    else:
        req = urllib2.urlopen(serveraddr + r'/' + word)
        self.update_dict_field(ix, req.read())
    # try:
    #     if use_local:
    #         showInfo("  fill: %d   query: %s "%(ix, dict_path))
    #         if not index_builders[ix]:
    #             index_mdx(ix)
    #         # index_mdx() if not index_builder else 0
    #         result = index_builder.mdx_lookup(word)
    #         showInfo(result[0])
    #         if result:
    #             self.update_dict_field(ix, result[0])
    #     else:
    #         req = urllib2.urlopen(serveraddr + r'/' + word)
    #         self.update_dict_field(ix, req.read())
    # except AssertionError as e:
    #     # no valid mdict file found.
    #     pass
    # except sqlite3.OperationalError:
    #     pass
    # except:
    #     # server error
    #     pass


def save_media_files(ib, *args, **kwargs):
    """
    only get the necessary static files
    ** kwargs: data = list
    """
    lst = []
    errors = []
    wild = list(args) + ['*' + os.path.basename(each) for each in kwargs.get('data', [])]
    for each in wild:
        keys = ib.get_mdd_keys(each)
        if not keys:
            errors.append(each)
        lst.extend(keys)
    # showInfo(str(errors))
    media_dir = mw.col.media.dir()
    for each in lst:
        try:
            bytes_list = ib.mdd_lookup(each)
            if bytes_list:
                savepath = os.path.join(
                    media_dir, '_' + os.path.basename(each))
                if not os.path.exists(savepath):
                    with open(savepath, 'wb') as f:
                        f.write(bytes_list[0])
        except sqlite3.OperationalError as e:
            showInfo(str(e))
    return errors


def convert_media_path(ib, html):
    """
    convert the media path to actual path in anki's collection media folder.'
    """
    lst = list()
    mcss = re.findall('href="(\S+?\.css)"', html)
    lst.extend(list(set(mcss)))
    mjs = re.findall('src="([\w\./]\S+?\.js)"', html)
    lst.extend(list(set(mjs)))
    msrc = re.findall('<img.*?src="([\w\./]\S+?)".*?>', html)
    lst.extend(list(set(msrc)))
    save_media_files(ib, data=list(set(msrc)))
    # showInfo(str(list(set(msrc))))
    # print lst
    newlist = ['_' + each.split('/')[-1] for each in lst]
    # print newlist
    for each in zip(lst, newlist):
        html = html.replace(each[0], each[1])
    return unicode(html)


def update_dict_field(self, idx, text, ib=0):
    note = self.editor.note
    # old_items = note.items()
    # item = list(note.items())[idx]
    note.fields[idx] = convert_media_path(ib, text) if ib else text


paras = read_parameters()
# showInfo(dictpath)
AddCards.query = query
AddCards.query_youdao = query_youdao
AddCards.query_mdict = query_mdict
AddCards.update_dict_field = update_dict_field
AddCards.setupButtons = wrap(AddCards.setupButtons, my_setupButtons, "before")
# create a new menu item, "test"
action = QAction("Word Query", mw)
# set it to call testFunction when it's clicked
action.triggered.connect(set_options)
# and add it to the tools menu
mw.form.menuTools.addAction(action)


deck_name = u"test"
note_type_name = u"MultiDicts"

expsdict = defaultdict(str)


def query_youdao2(word):
    d = defaultdict(str)
    result = urllib2.urlopen(
        "http://dict.youdao.com/fsearch?client=deskdict&keyfrom=chrome.extension&pos=-1&doctype=xml&xmlVersion=3.2&dogVersion=1.0&vendor=unknown&appVer=3.1.17.4208&le=eng&q=%s" % word, timeout=5).read()
    doc = xml.etree.ElementTree.parse(StringIO(result))
    symbol, uk_symbol, us_symbol = unicode(doc.findtext(".//phonetic-symbol")), unicode(doc.findtext(
        ".//uk-phonetic-symbol")), unicode(doc.findtext(".//us-phonetic-symbol"))
    d[u'英美音标'] = unicode(u'UK [%s] US [%s]' % (uk_symbol, us_symbol))
    d[u'简要中文释义'] = unicode('<br>'.join([node.text for node in doc.findall(
        ".//custom-translation/translation/content")]))
    return d


def query_mdict2(word):
    d = defaultdict(str)
    result = None
    if use_local:
        try:
            if not index_builder:
                index_mdx()
            result = index_builder.mdx_lookup(word)
            if result:
                d = update_field2(result[0])
        except AssertionError as e:
            # no valid mdict file found.
            pass
    if use_server:
        try:
            req = urllib2.urlopen(
                serveraddr + r'/' + word)
            result2 = req.read()
            if result2:
                d.update(update_field2(result2))
        except:
            # server error
            pass
    return d


def update_field2(result_text):
    d = defaultdict(str)
    result_text = convert_media_path(result_text)
    for rule in rules:
        feature = rule["feature"]
        if feature and feature in result_text:
            d[rule["name"]] = result_text
    return d


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


def batch_import2():
    """
    Use addNote method to add the note one by one, but it can't check if the card exists now.
    """
    # index_mdx()
    filepath = QFileDialog.getOpenFileName(
        caption="select words table file", directory=os.path.dirname(dictpath), filter="All Files(*.*)")
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

    with open('t.txt', 'wb') as fff:
        for data in queue:
            fff.write(','.join(data.values()) + '\n')
    # insert
    for data in queue:
        f = mw.col.newNote()
        for key in data:
            f[key] = data[key]
        mw.col.addNote(f)
    mw.reset()


class BatchQueryer(QThread):

    def __init__(self, filepath, queue):
        QThread.__init__(self)
        self.filepath = filepath
        self.queue = queue

    def run(self):
        with open(self.filepath, 'rb') as f:
            for i, line in enumerate(f):
                d = defaultdict(str)
                l = [each.strip() for each in line.split('\t')]
                word, sentence = l if len(l) == 2 else (l[0], "")
                if word:
                    m = re.search('\((.*?)\)', word)
                    if m:
                        word = m.groups()[0]
                    d[u'英语单词'] = unicode(word)
                    d[u'英语例句'] = unicode(sentence)
                    if enable_youdao == 1:
                        showInfo("enable youdao")
                        d.update(query_youdao2(word))
                    d.update(query_mdict2(word))
                    self.queue.append(d)


action = QAction("Batch Import...", mw)
# set it to call testFunction when it's clicked
action.triggered.connect(batch_import2)
# and add it to the tools menu
# mw.form.menuTools.addAction(action)
actionSep = QAction("", mw)
actionSep.setSeparator(True)
mw.form.menuCol.insertAction(mw.form.actionExit, actionSep)
mw.form.menuCol.insertAction(actionSep, action)

#-*- coding:utf-8 -*-

import sys

reload(sys)
sys.setdefaultencoding('utf8')
import anki
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
from aqt.utils import shortcut, showInfo, showText, tooltip
# import trackback
from mdict.mdict_query import IndexBuilder
import cPickle
from collections import defaultdict

index_builders = defaultdict(int)
savepath = os.path.join(sys.path[0], 'config')


def read_parameters():
    try:
        with open(savepath, 'rb') as f:
            paras = cPickle.load(f)
            if isinstance(paras, list):
                # 兼容之前的版本
                return paras, ''
            elif isinstance(paras, dict):
                return paras.get('maps', list()), paras.get('model', '')
            else:
                return list(), ''
    except:
        return list(), ''


def set_parameters():
    global maps
    cbs, les, lbs = mw.myWidget.findChildren(
        QCheckBox), mw.myWidget.findChildren(QLineEdit), mw.myWidget.findChildren(QLabel)
    maps = [{"checked": cb.isChecked(), "dict_path": le.text().strip(), "fld_name": lb.text()}
            for (cb, le, lb) in zip(cbs, les, lbs)]
    with open(savepath, 'wb') as f:
        cPickle.dump({'maps': maps, 'model': model_name}, f)


class MdxIndexer(QThread):

    def __init__(self, ix):
        QThread.__init__(self)
        self.ix = ix

    def run(self):
        if self.ix == -1:
            # index all dicts
            for i, each in enumerate(maps):
                if each['checked'] and each["dict_path"]:
                    index_builders[i] = self.work(each["dict_path"])
        else:
            # only index given dict, specified by ix
            index_builders[self.ix] = self.work(maps[self.ix]["dict_path"])

    def work(self, dict_path):
        # showInfo("%d, %s" % (self.ix, dict_path))
        if not dict_path.startswith("http://"):
            index_builder = IndexBuilder(dict_path)
            errors, styles = save_media_files(index_builder, '*.css', '*.js')
            # if '*.css' in errors:
            # info = ' '.join([each[2:] for each in ['*.css', '*.js'] if
            # each in errors ])
            # tooltip(u"%s字典中缺失css文件，格式显示可能不正确，请自行查找文件并放入媒体文件夹中" %
            #         (dict_path), period=3000)
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
        for i, each in enumerate(maps):
            add_dict_layout(i, **each)
    mw.myWidget.setLayout(mw.myMainLayout)


def show_models():
    ret = StudyDeck(
        mw, names=lambda: sorted(mw.col.models.allNames()), accept=_("Choose"), title=_("Choose Note Type"),
        help="_notes", parent=mw.myWidget,
        cancel=True, geomKey="selectModel")
    if ret.name:
        model = mw.col.models.byName(ret.name)
        global model_name
        model_name = ret.name
        mw.myChooseButton.setText(u'选择笔记类型 [当前类型 -- %s]' % ret.name)
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
    choose_btn = QPushButton(u"选择")
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
    mw.myWidget = widget = QWidget()
    mw.myMainLayout = main_layout = QVBoxLayout()
    models_layout = QHBoxLayout()
    mw.myScrollArea = scroll_area = QScrollArea()
    mw.myDictsWidget = dicts_widget = QWidget()
    mw.myDictsLayout = dicts_layout = QVBoxLayout(scroll_area)
    dicts_widget.setLayout(dicts_layout)
    scroll_area.setWidget(dicts_widget)
    scroll_area.setWidgetResizable(True)
    mw.signal_mapper_sel = QSignalMapper(mw.myWidget)
    mw.signal_mapper_chk = QSignalMapper(mw.myWidget)
    # mw.myModelNameLabel = QLabel(u"笔记类型")
    mw.myChooseButton = models_button = QPushButton(u"选择笔记类型")
    models_button.clicked.connect(btn_models_pressed)
    if model_name:
        models_button.setText(u'选择笔记类型 [当前类型 -- %s]' % model_name)
    models_layout.addWidget(models_button)
    # build fields -- dicts layout
    if maps:
        build_layout()
    ok_button = QPushButton(u"确认")
    ok_button.clicked.connect(btn_ok_pressed)
    main_layout.addLayout(models_layout)
    main_layout.addWidget(scroll_area)
    # main_layout.addLayout(dicts_layout)
    main_layout.addWidget(ok_button)
    mw.signal_mapper_sel.mapped.connect(select_dict)
    mw.signal_mapper_chk.mapped.connect(chkbox_state_changed)
    widget.setLayout(main_layout)
    widget.show()


# def setupEditor(self):
#     query_btn = QPushButton("Query2")
#     self.form.horizontalLayout.insertWidget(
#         -1, query_btn)


# AddCards.setupChoosers = wrap(AddCards.setupChoosers, setupEditor, "before")

def my_setupButtons(self):
    bb = self.form.buttonBox
    ar = QDialogButtonBox.ActionRole
    self.queryButton = bb.addButton(_(u"查询"), ar)
    self.queryButton.clicked.connect(self.query)
    self.queryButton.setShortcut(QKeySequence("Ctrl+Q"))
    self.queryButton.setToolTip(shortcut(_(u"查询 (shortcut: ctrl+q)")))


def query(self):
    for field in self.editor.note.fields:
        field = ''
    for i, each in enumerate(maps):
        if each['checked'] and each['dict_path'].strip():
            self.query_mdict(i, **each)
    self.editor.setNote(self.editor.note, focus=True)


# def query_youdao(self):
#     note = self.editor.note
#     word = note.fields[0]      # choose the first field as the word
#     # showInfo('youdoa:%s'%word)
#     result = urllib2.urlopen(
#         "http://dict.youdao.com/fsearch?client=deskdict&keyfrom=chrome.extension&pos=-1&doctype=xml&xmlVersion=3.2&dogVersion=1.0&vendor=unknown&appVer=3.1.17.4208&le=eng&q=%s" % word, timeout=5).read()
#     file = StringIO(result)
#     doc = xml.etree.ElementTree.parse(file)
#     # fetch symbols
#     symbol, uk_symbol, us_symbol = doc.findtext(".//phonetic-symbol"), doc.findtext(
#         ".//uk-phonetic-symbol"), doc.findtext(".//us-phonetic-symbol")
#     # showInfo(','.join([symbol, uk_symbol, us_symbol]))
#     try:
#         note.fields[1] = 'UK [%s] US [%s]' % (uk_symbol, us_symbol)
#         # fetch explanations
#         note.fields[3] = '<br>'.join([node.text for node in doc.findall(
#             ".//custom-translation/translation/content")])
#     except:
#         showInfo("Template Error, online!")


def query_mdict(self, ix, **kwargs):
    note = self.editor.note
    word = note.fields[0]      # choose the first field as the word
    result = None
    self.update_dict_field(ix, "")
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
            # showInfo('ssssssss  %s' % result[0])
            self.update_dict_field(ix, str(result[0]), index_builders[ix])
    else:
        req = urllib2.urlopen(dict_path + r'/' + word)
        # showInfo(req.read())
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


def update_dict_field(self, idx, text, ib=0):
    # showInfo('before: %d %d, %s' % (idx, len(text), text))
    note = self.editor.note
    # old_items = note.items()
    # item = list(note.items())[idx]
    note.fields[idx] = convert_media_path(ib, text) if ib else text


def save_media_files(ib, *args, **kwargs):
    """
    only get the necessary static files
    ** kwargs: data = list
    """
    lst = []
    errors = []
    styles = []
    wild = list(args) + ['*' + os.path.basename(each)
                         for each in kwargs.get('data', [])]
    try:
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
                    if os.path.basename(each).endswith('.css') or os.path.basename(each).endswith('.js'):
                        styles.append(os.path.basename(each))
                    if not os.path.exists(savepath):
                        with open(savepath, 'wb') as f:
                            f.write(bytes_list[0])
            except sqlite3.OperationalError as e:
                showInfo(str(e))
        # showInfo(str(styles))
    except AttributeError:
        '''
        有些字典会出这样的错误u AttributeError: 'IndexBuilder' object has no attribute '_mdd_db'
        '''
        pass
    return errors, styles


def convert_media_path(ib, html):
    """
    convert the media path to actual path in anki's collection media folder.'
    """
    # showInfo('%s %s' % (type(html), str(html)))
    lst = list()
    mcss = re.findall('href="(\S+?\.css)"', html)
    lst.extend(list(set(mcss)))
    mjs = re.findall('src="([\w\./]\S+?\.js)"', html)
    lst.extend(list(set(mjs)))
    msrc = re.findall('<img.*?src="([\w\./]\S+?)".*?>', html)
    lst.extend(list(set(msrc)))
    errors, styles = save_media_files(ib, data=list(set(lst)))
    # showInfo(str(styles))
    # showInfo(str(list(set(msrc))))
    # print lst
    newlist = ['_' + each.split('/')[-1] for each in lst]
    # print newlist
    for each in zip(lst, newlist):
        html = html.replace(each[0], each[1])
    html = '<br>'.join(["<style>@import url('_%s');</style>" %
                        style for style in styles if style.endswith('.css')]) + html
    html += '<br>'.join(['<script type="text/javascript" src="_%s"></script>' %
                         style for style in styles if style.endswith('.js')])
    # showInfo(str(html))
    # showInfo(html)
    return unicode(html)


maps, model_name = read_parameters()

AddCards.query = query
# AddCards.query_youdao = query_youdao
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


# def query_youdao2(word):
#     d = defaultdict(str)
#     result = urllib2.urlopen(
#         "http://dict.youdao.com/fsearch?client=deskdict&keyfrom=chrome.extension&pos=-1&doctype=xml&xmlVersion=3.2&dogVersion=1.0&vendor=unknown&appVer=3.1.17.4208&le=eng&q=%s" % word, timeout=5).read()
#     doc = xml.etree.ElementTree.parse(StringIO(result))
#     symbol, uk_symbol, us_symbol = unicode(doc.findtext(".//phonetic-symbol")), unicode(doc.findtext(
#         ".//uk-phonetic-symbol")), unicode(doc.findtext(".//us-phonetic-symbol"))
#     d[u'英美音标'] = unicode(u'UK [%s] US [%s]' % (uk_symbol, us_symbol))
#     d[u'简要中文释义'] = unicode('<br>'.join([node.text for node in doc.findall(
#         ".//custom-translation/translation/content")]))
#     return d


def query_mdict2(word, ix, **kwargs):
    dict_path, fld_name = kwargs.get(
        'dict_path', '').strip(), kwargs.get('fld_name', '').strip()
    use_server = dict_path.startswith("http://")
    use_local = not use_server
    if use_local:
        if not index_builders[ix]:
            index_mdx(ix)
        result = index_builders[ix].mdx_lookup(word)
        if result:
            return update_dict_field2(ix, result[0], index_builders[ix])
    else:
        req = urllib2.urlopen(serveraddr + r'/' + word)
        return update_dict_field2(ix, req.read())
    return ""
    # showInfo(str(d))


def update_dict_field2(idx, text, ib=0):
    return convert_media_path(ib, text) if ib else text


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
        for ix, each in enumerate(maps):
            fld_name = maps[ix]['fld_name']
            if ix == 0:
                note[fld_name] = word.decode('utf-8')
            else:
                note[fld_name] = data[ix].decode('utf-8')
        numbers += mw.col.addNote(note)
    tooltip(u'共批量导入%d张笔记' % numbers)
    mw.reset()


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
                    for i, each in enumerate(maps):
                        # 根据设置好的字段和字典的映射关系，轮询取每个字典的释义
                        if each['checked'] and each['dict_path'].strip():
                            d[i] = query_mdict2(word, i, **each)
                    self.queue.append((word, d))


action = QAction("Batch Import...", mw)
action.triggered.connect(batch_import2)
actionSep = QAction("", mw)
actionSep.setSeparator(True)
mw.form.menuCol.insertAction(mw.form.actionExit, actionSep)
mw.form.menuCol.insertAction(actionSep, action)


def browser_menus():
    """
    Gives user access to mass generator, MP3 stripper, and the hook that
    disables and enables it upon selection of items.
    """

    # from PyQt4 import QtGui

    def on_setup_menus(browser):
        """Create an AwesomeTTS menu and add browser actions to it."""

        menu = QtGui.QMenu("WordQuery", browser.form.menubar)
        browser.form.menubar.addMenu(menu)

        gui.Action(
            target=Bundle(
                constructor=gui.BrowserGenerator,
                args=(),
                kwargs=dict(browser=browser,
                            addon=addon,
                            alerts=aqt.utils.showWarning,
                            ask=aqt.utils.getText,
                            parent=browser),
            ),
            text="&Add Audio to Selected...",
            sequence=sequences['browser_generator'],
            parent=menu,
        )
        gui.Action(
            target=Bundle(
                constructor=gui.BrowserStripper,
                args=(),
                kwargs=dict(browser=browser,
                            addon=addon,
                            alerts=aqt.utils.showWarning,
                            parent=browser),
            ),
            text="&Remove Audio from Selected...",
            sequence=sequences['browser_stripper'],
            parent=menu,
        )

    def update_title_wrapper(browser):
        """Enable/disable AwesomeTTS menu items upon selection."""

        enabled = bool(browser.form.tableView.selectionModel().selectedRows())
        for action in browser.findChildren(gui.Action):
            action.setEnabled(enabled)

    anki.hooks.addHook(
        'browser.setupMenus',
        on_setup_menus,
    )

    aqt.browser.Browser.updateTitle = anki.hooks.wrap(
        aqt.browser.Browser.updateTitle,
        update_title_wrapper,
        'before',
    )

focus_word = ''
focus_editor = None

query_result = ''


def query3():
    mw.progress.start(immediate=True, label="Querying...")
    for field in focus_editor.note.fields:
        field = ''
    for i, each in enumerate(maps):
        if each['checked'] and each['dict_path'].strip():
            res = query_mdict3(i, **each)
            focus_editor.note.fields[i] = res
    focus_editor.setNote(focus_editor.note, focus=True)
    mw.progress.finish()


def query_mdict3(ix, **kwargs):
    note = focus_editor.note
    word = note.fields[0]      # choose the first field as the word
    dict_path, fld_name = kwargs.get(
        'dict_path', '').strip(), kwargs.get('fld_name', '').strip()
    use_server = dict_path.startswith("http://")
    use_local = not use_server
    if use_local:
        if not index_builders[ix]:
            index_mdx(ix)
        result = index_builders[ix].mdx_lookup(word)
        if result:
            tt = update_dict_field2(ix, result[0], index_builders[ix])
            return tt
    else:
        req = urllib2.urlopen(serveraddr + r'/' + word)
        return update_dict_field2(ix, req.read())
    return ""


def add_context_menu(web_view, menu):
    note = web_view.editor.note
    current_field = web_view.editor.currentField
    global focus_word
    focus_word = note.fields[current_field]
    global focus_editor
    focus_editor = web_view.editor
    action_query_button = QPushButton("Query")
    action_query_button.clicked.connect(query3)
    submenu = QMenu("WordQuery", menu)
    submenu.addAction(
        "Word Query",
        lambda: action_query_button.click() if action_query_button.isEnabled()
        else aqt.utils.showWarning(
            "Select the note field to which you want query",
            web_view.window,
        )
    )
    needs_separator = True
    menu.addMenu(submenu)


# anki.hooks.addHook('AnkiWebView.contextMenuEvent', add_context_menu)
anki.hooks.addHook('EditorWebView.contextMenuEvent', add_context_menu)
# anki.hooks.addHook('Reviewer.contextMenuEvent',
#                    lambda reviewer, menu:
#                    add_context_menu(reviewer.web, menu))

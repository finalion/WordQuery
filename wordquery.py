# import the main window object (mw) from aqt
# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.
import os
import re
import sys
import urllib2
import xml.etree.ElementTree
from StringIO import StringIO

import aqt
from anki.hooks import addHook, runHook, wrap
from anki.importing import TextImporter
from aqt import mw
from aqt.addcards import AddCards
from aqt.qt import *
from aqt.toolbar import Toolbar
# import the "show info" tool from utils.py
from aqt.utils import shortcut, showInfo
from mdict.mdict_query import IndexBuilder


default_server = 'http://127.0.0.1:8000'
index_builder = None
dictpath = ''
savepath = os.path.join(sys.path[0], 'config')
serveraddr = default_server
use_local, use_server = False, False
# showInfo(sys.path[0])
# showInfo(savepath)
# custom Toolbar


def _my_center_links(self):
    '''
    todo: use wrap
    '''
    links = [
            ["decks", _("Decks"), _("Shortcut key: %s") % "D"],
            ["add", _("Add"), _("Shortcut key: %s") % "A"],
            ["browse", _("Browse"), _("Shortcut key: %s") % "B"],
            ["query", _("Query"), _("Shortcut key: %s") % "Q"],
    ]
    self.link_handlers["query"] = show_query_window  # self._queryLinkHandler
    # showInfo("custorm links")
    return self._linkHTML(links)
Toolbar._centerLinks = _my_center_links

# build set dialog and process the dict path


def select_dict():
    global dictpath
    dictpath = QFileDialog.getOpenFileName(
        caption="select dictionary", directory=os.path.dirname(dictpath), filter="mdx Files(*.mdx)")
    if dictpath:
        mw.myEditLocalPath.setText(dictpath)


def okbtn_pressed():
    mw.myWidget.close()
    set_parameters()
    index_mdx()


def set_parameters():
    global dictpath, serveraddr, use_local, use_server
    dictpath = mw.myEditLocalPath.text()
    serveraddr = mw.myEditServerAddr.text()
    use_local = mw.myCheckLocal.isChecked()
    use_server = mw.myCheckServer.isChecked()
    with open(savepath, 'wb') as f:
        f.write('%d|%s|%d|%s'.encode('utf-8') %
                (use_local, dictpath, use_server, serveraddr))


def read_parameters():
    # showInfo(savepath)
    # with open(savepath, 'rb') as f:
    #     uls, path, uss, addr = f.read().strip().split('|')
    #     showInfo('%s,%s,%s,%s' % (uls, path, uss, addr))
    #     return bool(int(uls)), path, bool(int(uss)), addr
    try:
        with open(savepath, 'rb') as f:
            uls, path, uss, addr = f.read().strip().split('|')
            return bool(int(uls)), path, bool(int(uss)), addr
    except:
        # showInfo("not exist")
        return False, "", False, default_server


class MdxIndexer(QThread):

    def __init__(self):
        QThread.__init__(self)

    def run(self):
        global index_builder
        index_builder = IndexBuilder(dictpath)


def index_mdx():
    mw.progress.start(immediate=True, label="Index building...")
    index_thread = MdxIndexer()
    index_thread.start()
    while not index_thread.isFinished():
        mw.app.processEvents()
        index_thread.wait(100)
    mw.progress.finish()


def onCheckLocalStageChanged():
    global use_local
    use_local = mw.myCheckLocal.isChecked()
    if use_local:
        select_dict()


def onCheckServerStageChanged():
    global use_server
    use_server = mw.myCheckServer.isChecked()


def set_options():
    mw.myWidget = widget = QWidget()
    layout = QGridLayout()

    mw.myCheckLocal = check_local = QCheckBox("Use Local Dict")
    check_local.setChecked(use_local)
    check_local.stateChanged.connect(onCheckLocalStageChanged)
    mw.myEditLocalPath = path_edit = QLineEdit()
    path_edit.setText(dictpath)

    mw.myCheckServer = check_server = QCheckBox("Use MDX Server")
    check_server.setChecked(use_server)
    check_local.stateChanged.connect(onCheckServerStageChanged)
    mw.myEditServerAddr = server_edit = QLineEdit()
    server_edit.setText(serveraddr)

    ok_button = QPushButton("OK")
    ok_button.clicked.connect(okbtn_pressed)
    # layout.addWidget(QLabel("Set dictionary path: "))
    layout.addWidget(check_local, 0, 0)
    layout.addWidget(path_edit, 0, 1)
    layout.addWidget(check_server, 1, 0)
    layout.addWidget(server_edit, 1, 1)
    layout.addWidget(ok_button, 2, 0)
    widget.setLayout(layout)
    widget.show()


#######################################################

# "Query" Link in main window


def query_word():
    word = mw.myWordEdit.text().strip()
    if word:
        # showInfo("Query %s" % word)
        mw.myWebView.load(
            QUrl('http://dict.baidu.com/s?wd=%s&ptype=english' % word))


def show_query_window():
    mw.myWidget = widget = QWidget()
    layout = QGridLayout()
    mw.myWordEdit = word_edit = QLineEdit()
    ok_button = QPushButton("OK")
    ok_button.clicked.connect(query_word)
    mw.myWebView = result_view = QWebView()
    layout.addWidget(QLabel("Word to query: "))
    layout.addWidget(word_edit)
    layout.addWidget(ok_button)
    layout.addWidget(result_view)

    widget.setLayout(layout)
    widget.show()
#################################################################

# custom add ui


def my_setupButtons(self):
    bb = self.form.buttonBox
    ar = QDialogButtonBox.ActionRole
    self.queryButton = bb.addButton(_("Query"), ar)
    self.queryButton.clicked.connect(self.query)
    self.queryButton.setShortcut(QKeySequence("Ctrl+Q"))
    self.queryButton.setToolTip(shortcut(_("Query (shortcut: ctrl+q)")))
    # fa = str(self.form.fieldsArea.childAt(QPoint(0, 0)).text())
    # showInfo(fa)


def query(self):
    for field in self.editor.note.fields:
        field = ''
    self.query_youdao()
    self.query_mdict()
    self.editor.currentField = 0
    self.editor.loadNote()


def query_youdao(self):
    self.editor.saveAddModeVars()
    note = self.editor.note
    # note = self.addNote(note)
    word = note.fields[0]      # choose the first field as the word
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
        note.fields[2] = '<br>'.join([node.text for node in doc.findall(
            ".//custom-translation/translation/content")])
    except:
        showInfo("Template Error!")


def query_mdict(self):
    self.editor.saveAddModeVars()
    note = self.editor.note
    word = note.fields[0]      # choose the first field as the word
    result = None
    if use_local:
        try:
            if not index_builder:
                index_mdx()
            result = index_builder.mdx_lookup(word)
            if result:
                update_field(result[0], note)
        except AssertionError as e:
            # no valid mdict file found.
            pass
    if use_server:
        try:
            req = urllib2.urlopen(
                serveraddr + r'/' + word)
            result2 = req.read()
            if result2:
                update_field(result2, note)
        except:
            # server error
            pass


def update_field(result_text, note):
    if len(note.fields) < 15:
        showInfo("Template Error!")
        return
    if 'href="O8C.css"' in result_text:
        note.fields[9] = result_text
    elif 'href="ODE.css"' in result_text:
        note.fields[10] = result_text
    elif 'href="MacmillanEnEn.css"' in result_text:
        # result_text = re.sub(
        #     '<a href=".*?>(.*?)</a>', r'\1', result_text)
        # result_text = re.sub(
        #     '<p class="example">(.*?)</p>', r'\1', result_text)
        # result_text = re.sub(
        #     '<span class="example">(.*?)</span>', r'\1', result_text)
        note.fields[11] = result_text
    elif 'href="LDOCE6.css"' in result_text:
        note.fields[12] = result_text.replace(
            '<img src="img/spkr_r.png">', '').replace(
            '<img src="img/spkr_b.png">', '').replace(
            '<img src="img/spkr_g.png">', '')
    else:
        # collins stars
        mstars = re.search(
            '<span class="C1_word_header_star">(.*?)</span>', result_text)
        if mstars:
            note.fields[7] = mstars.groups()[0]
        # collins explanations
        adapt_to_tempalate = lambda text: text.replace(
            'class="C1_', 'class="')
        mexplains = re.search('(<div class="tab_content".*</div>)',
                              result_text, re.DOTALL)
        if mexplains:
            note.fields[8] = adapt_to_tempalate(mexplains.groups()[0])
            # showInfo(mexplains.groups()[0])


use_local, dictpath, use_server, serveraddr = read_parameters()
# showInfo(dictpath)
AddCards.query = query
AddCards.query_youdao = query_youdao
AddCards.query_mdict = query_mdict
AddCards.setupButtons = wrap(AddCards.setupButtons, my_setupButtons, "before")

# create a new menu item, "test"
action = QAction("Word Query", mw)
# set it to call testFunction when it's clicked
action.triggered.connect(set_options)
# and add it to the tools menu
mw.form.menuTools.addAction(action)

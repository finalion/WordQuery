# import the main window object (mw) from aqt
import aqt
from aqt import mw
from aqt.toolbar import Toolbar
# import the "show info" tool from utils.py
from aqt.utils import showInfo, shortcut
# import all of the Qt GUI library
from aqt.qt import *
from anki.importing import TextImporter
from anki.hooks import addHook, wrap, runHook
from aqt.addcards import AddCards
# We're going to add a menu item below. First we want to create a function to
# be called when the menu item is activated.
import os
import sys
import re
import xml.etree.ElementTree
import urllib2
from StringIO import StringIO
from mdict.mdict_query import IndexBuilder

dictpath = ''
savepath = os.path.join(sys.path[0], 'dictpath')
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
        caption="select dictionary", directory=sys.path[0], filter="mdx Files(*.mdx)")
    if dictpath:
        mw.myPathedit.setText(dictpath)


def okbtn_pressed():
    mw.myWidget.close()
    set_path()


def set_path():
    global dictpath
    dictpath = mw.myPathedit.text()
    # if not dictpath.endswith('\\'):
    #     dictpath += '\\'
    with open(savepath, 'wb') as f:
        f.write(dictpath.encode('utf-8'))


def read_path():
    # showInfo(savepath)
    try:
        with open(savepath, 'rb') as f:
            path = f.read().strip()
            return path
    except:
        showInfo("not exist")
        return ""


def set_options():
    mw.myWidget = widget = QWidget()
    layout = QGridLayout()
    mw.myPathedit = path_edit = QLineEdit()
    path_edit.setText(dictpath)
    mw.seldict_button = seldict_button = QPushButton("Select")
    seldict_button.clicked.connect(select_dict)
    ok_button = QPushButton("OK")
    ok_button.clicked.connect(okbtn_pressed)
    layout.addWidget(QLabel("Set dictionary path: "))
    layout.addWidget(path_edit)
    layout.addWidget(seldict_button)
    layout.addWidget(ok_button)
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
    pass


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
    pass
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
        "http://dict.youdao.com/fsearch?client=deskdict&keyfrom=chrome.extension&pos=-1&doctype=xml&xmlVersion=3.2&dogVersion=1.0&vendor=unknown&appVer=3.1.17.4208&le=eng&q=%s" % word).read()
    file = StringIO(result)
    doc = xml.etree.ElementTree.parse(file)
    # fetch symbols
    symbol, uk_symbol, us_symbol = doc.findtext(".//phonetic-symbol"), doc.findtext(
        ".//uk-phonetic-symbol"), doc.findtext(".//us-phonetic-symbol")
    # showInfo(','.join([symbol, uk_symbol, us_symbol]))
    note.fields[1] = 'UK [%s] US [%s]' % (uk_symbol, us_symbol)
    # fetch explanations
    note.fields[2] = '<br>'.join([node.text for node in doc.findall(
        ".//custom-translation/translation/content")])


def query_mdict(self):
    self.editor.saveAddModeVars()
    note = self.editor.note
    # note = self.addNote(note)
    word = note.fields[0]      # choose the first field as the word
    try:
        # dictpath = read_path()
        # showInfo(dictpath)
        builder = IndexBuilder(dictpath)
        result_text = builder.mdx_lookup(word)
        # showInfo(str(result_text))
        # collins stars
        mstars = re.search(
            '<span class="C1_word_header_star">(.*?)</span>', result_text[0])
        if mstars:
            note.fields[7] = mstars.groups()[0]
        # collins explanations

        def adapt_to_tempalate(text):
            return text.replace('class="C1_', 'class="')
        mexplains = re.search('(<div class="tab_content".*</div>)',
                              result_text[0], re.DOTALL)
        if mexplains:
            note.fields[8] = adapt_to_tempalate(mexplains.groups()[0])
            # showInfo(mexplains.groups()[0])
    except AssertionError as e:
        # no valid mdict file found.
        pass

dictpath = read_path()
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

#-*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import anki
import aqt
from aqt import mw
from aqt.qt import *
from anki.hooks import addHook, runHook, wrap
from aqt.addcards import AddCards
from aqt.utils import shortcut, showInfo, showText, tooltip
# import trackback
import cPickle
from collections import defaultdict
from wquery.ui import show_options
from wquery.batch import batch_import
from wquery.query import query, query_from_bmenu, query_from_cmenu, query_from_btn
import wquery.context as c


def read_parameters():
    try:
        with open(c.savepath, 'rb') as f:
            c.mappings = cPickle.load(f)
            try:
                c.model_id = c.mappings['last']
                c.maps = c.mappings[c.model_id]
            except:
                c.maps, c.model_id = list(), 0

    except:
        c.mappings = defaultdict(list)
        c.maps, c.model_id = list(), 0


def add_query_button(self):
    bb = self.form.buttonBox
    ar = QDialogButtonBox.ActionRole
    self.queryButton = bb.addButton(_(u"Query"), ar)
    self.queryButton.clicked.connect(query_from_btn)
    c.focus_editor = self.editor
    self.queryButton.setShortcut(QKeySequence("Ctrl+Q"))
    self.queryButton.setToolTip(shortcut(_(u"Query (shortcut: ctrl+q)")))


def setup_browser_menu():

    def on_setup_menus(browser):
        menu = QMenu("WordQuery", browser.form.menubar)
        c.focus_browser = browser
        c.focus_editor = c.focus_browser.editor
        browser.form.menubar.addMenu(menu)
        action_queryselected = QAction("Query Selected", browser)
        action_queryselected.triggered.connect(query_from_bmenu)
        action_queryselected.setShortcut(QKeySequence("Ctrl+Q"))
        action_options = QAction("Options", browser)
        action_options.triggered.connect(show_options)
        menu.addAction(action_queryselected)
        menu.addAction(action_options)

    anki.hooks.addHook('browser.setupMenus', on_setup_menus)


def setup_context_menu():
    def on_setup_menus(web_view, menu):
        """
        add context menu to webview
        """
        c.focus_editor = web_view.editor
        c.model_id = c.focus_editor.note.model()['id']
        c.maps = c.mappings[c.model_id]
        action = menu.addAction(_("Query"))
        action.triggered.connect(query_from_cmenu)
        needs_separator = True
        # menu.addMenu(submenu)

    anki.hooks.addHook('EditorWebView.contextMenuEvent', on_setup_menus)


def setup_batchimport_menu():
    # add batch import submenu to File menu
    action = QAction("Batch Import...", mw)
    action.triggered.connect(batch_import)
    actionSep = QAction("", mw)
    actionSep.setSeparator(True)
    mw.form.menuCol.insertAction(mw.form.actionExit, actionSep)
    mw.form.menuCol.insertAction(actionSep, action)


def customize_addcards():
    AddCards.setupButtons = wrap(
        AddCards.setupButtons, add_query_button, "before")


def setup_options_menu():
    # add options submenu to Tools menu
    action = QAction("Word Query", mw)
    action.triggered.connect(show_options)
    mw.form.menuTools.addAction(action)

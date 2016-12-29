#-*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import anki
import aqt
from aqt import mw
from aqt.qt import *
from anki.hooks import addHook, wrap
from aqt.addcards import AddCards
from aqt.utils import showInfo, shortcut
import cPickle
from collections import defaultdict
from wquery.ui import show_options, start_services
from wquery.query import query_from_menu, query_from_editor
from wquery.context import context, config

have_setup = False


def add_query_button(self):
    bb = self.form.buttonBox
    ar = QDialogButtonBox.ActionRole
    context['editor'] = self.editor
    self.queryButton = bb.addButton(_(u"Query"), ar)
    self.queryButton.clicked.connect(query_from_editor)
    self.queryButton.setShortcut(QKeySequence("Ctrl+Q"))
    self.queryButton.setToolTip(shortcut(_(u"Query (shortcut: ctrl+q)")))


def setup_browser_menu():

    def on_setup_menus(browser):
        context['browser'] = browser
        menu = QMenu("WordQuery", browser.form.menubar)
        browser.form.menubar.addMenu(menu)
        action_queryselected = QAction("Query Selected", browser)
        action_queryselected.triggered.connect(query_from_menu)
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
        context['editor'] = web_view.editor
        if web_view.editor.currentField == 0:  # 只在第一项加右键菜单
            action = menu.addAction(_("Query"))
            action.triggered.connect(query_from_editor)
            needs_separator = True
        else:
            action = menu.addAction(_("Query Current"))
            action.triggered.connect(query_from_editor)
            needs_separator = True
            # menu.addMenu(submenu)
    anki.hooks.addHook('EditorWebView.contextMenuEvent', on_setup_menus)
    shortcuts = [("Ctrl+Q", query), ]
    anki.hooks.addHook('setupEditorShortcuts', shortcuts)


def customize_addcards():
    AddCards.setupButtons = wrap(
        AddCards.setupButtons, add_query_button, "before")


def setup_options_menu():
    # add options submenu to Tools menu
    action = QAction("WordQuery...", mw)
    action.triggered.connect(show_options)
    mw.form.menuTools.addAction(action)
    global have_setup
    have_setup = True

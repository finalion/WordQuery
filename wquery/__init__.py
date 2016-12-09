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
from aqt.utils import shortcut, showInfo, showText, tooltip
import cPickle
from collections import defaultdict
from wquery.ui import show_options
from wquery.query import query_from_menu, query_from_editor
import wquery.context as c



def _show_mappings():
    s = ''
    for id, maps in c.mappings.items():
        if id == 'last':
            continue
        s += str(id) + ', '
        for each in maps:

            s += each['fld_name'] + ', '
        s += '\n--------\n'
    showText(s)


def mode_changed():
    model_id = mw.col.models.current()['id']
    if c.mappings.has_key(model_id):
        c.model_id = model_id
        c.maps = c.mappings[model_id]
        # showText(str(c.mappings))
        # showInfo('having ' + str(c.model_id) + ', ' +
        #          '\n '.join([each['fld_name'] for each in c.maps]))
    # else:
        # showInfo(str(c.model_id))
        # showInfo('not have %d' % c.model_id)
        # _show_mappings()

# addHook('currentModelChanged', mode_changed)


def read_parameters():
    try:
        with open(c.cfgpath, 'rb') as f:
            c.mappings = cPickle.load(f)
            # c.mappings = {for k,v in c.mappings.items()}
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
    c.context['editor'] = self.editor
    self.queryButton = bb.addButton(_(u"Query"), ar)
    self.queryButton.clicked.connect(query_from_editor)
    self.queryButton.setShortcut(QKeySequence("Ctrl+Q"))
    self.queryButton.setToolTip(shortcut(_(u"Query (shortcut: ctrl+q)")))


def setup_browser_menu():

    def on_setup_menus(browser):
        c.context['browser'] = browser
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
        c.context['editor'] = web_view.editor
        c.model_id = web_view.editor.note.model()['id']
        c.maps = c.mappings[c.model_id]
        if web_view.editor.currentField == 0:  # 只在第一项加右键菜单
            action = menu.addAction(_("Query"))
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

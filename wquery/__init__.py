#-*- coding:utf-8 -*-
#
# Copyright © 2016–2017 Liang Feng <finalion@gmail.com>
#
# Support: Report an issue at https://github.com/finalion/WordQuery/issues
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version; http://www.gnu.org/copyleft/gpl.html.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

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
from wquery.ui import show_options
from wquery.query import query_from_browser, query_from_editor_all_fields, query_from_editor_current_field
from wquery.context import context, config
from wquery.service import start_services


have_setup = False
my_shortcut = ''


def set_shortcut(key_sequence):
    global my_shortcut
    my_shortcut = key_sequence


def add_query_button(self):
    bb = self.form.buttonBox
    ar = QDialogButtonBox.ActionRole
    context['editor'] = self.editor
    self.queryButton = bb.addButton(_(u"Query"), ar)
    self.queryButton.clicked.connect(query_from_editor_all_fields)
    self.queryButton.setShortcut(QKeySequence(my_shortcut))
    self.queryButton.setToolTip(
        shortcut(_(u"Query (shortcut: %s)" % my_shortcut)))


def setup_browser_menu():

    def on_setup_menus(browser):
        context['browser'] = browser
        menu = QMenu("WordQuery", browser.form.menubar)
        browser.form.menubar.addMenu(menu)
        action_queryselected = QAction("Query Selected", browser)
        action_queryselected.triggered.connect(query_from_browser)
        action_queryselected.setShortcut(QKeySequence(my_shortcut))
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
        wqmenu = menu.addMenu('Word Query')
        action1 = wqmenu.addAction('Query All Fields')
        action2 = wqmenu.addAction('Query Current Field')
        action3 = wqmenu.addAction('Options')
        action1.triggered.connect(query_from_editor_all_fields)
        action2.triggered.connect(query_from_editor_current_field)
        action3.triggered.connect(show_options)
        needs_separator = True
        # menu.addMenu(submenu)
    anki.hooks.addHook('EditorWebView.contextMenuEvent', on_setup_menus)
    shortcuts = [(my_shortcut, query), ]
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

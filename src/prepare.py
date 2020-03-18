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


import anki
import aqt
from aqt import mw
from aqt.qt import *
from anki.hooks import addHook, wrap
from aqt.addcards import AddCards
from aqt.utils import showInfo, shortcut
from .query import query_from_browser, query_from_editor_all_fields, query_from_editor_current_field
from .context import config, app_icon
from .gui import dialogs

############## other config here ##################
# update all fields ignoring the original field content
update_all = False
# shortcut
my_shortcut = 'Ctrl+Q'
###################################################

have_setup = False

def show_options_dlg():
    dlg = dialogs.OptionsDlg(mw)
    dlg.exec_()
    dlg.activateWindow()
    dlg.raise_()


def query_decor(func, obj):
    def callback():
        return func(obj)
    return callback


def add_query_button(self):
    bb = self.form.buttonBox
    ar = QDialogButtonBox.ActionRole
    self.queryButton = bb.addButton(_(u"Query"), ar)
    self.queryButton.clicked.connect(query_decor(
        query_from_editor_all_fields, self.editor))
    self.queryButton.setShortcut(QKeySequence(my_shortcut))
    self.queryButton.setToolTip(
        shortcut(_(u"Query (shortcut: %s)" % my_shortcut)))


def setup_browser_menu():

    def on_setup_menus(browser):
        menu = QMenu("WordQuery", browser.form.menubar)
        browser.form.menubar.addMenu(menu)
        action_queryselected = QAction("Query Selected", browser)
        action_queryselected.triggered.connect(query_decor(
            query_from_browser, browser))
        action_queryselected.setShortcut(QKeySequence(my_shortcut))
        action_options = QAction("Options", browser)
        action_options.triggered.connect(show_options_dlg)
        menu.addAction(action_queryselected)
        menu.addAction(action_options)

    anki.hooks.addHook('browser.setupMenus', on_setup_menus)


def setup_context_menu():

    def on_setup_menus(web_view, menu):
        """
        add context menu to webview
        """
        wqmenu = menu.addMenu('Word Query')
        action1 = wqmenu.addAction('Query All Fields')
        action2 = wqmenu.addAction('Query Current Field')
        action3 = wqmenu.addAction('Options')
        action1.triggered.connect(query_decor(
            query_from_editor_all_fields, web_view.editor))
        action2.triggered.connect(query_decor(
            query_from_editor_current_field, web_view.editor))
        action3.triggered.connect(show_options_dlg)
        needs_separator = True
        # menu.addMenu(submenu)
    anki.hooks.addHook('EditorWebView.contextMenuEvent', on_setup_menus)
    # shortcuts = [(my_shortcut, query), ]
    # anki.hooks.addHook('setupEditorShortcuts', shortcuts)


def customize_addcards():
    AddCards.setupButtons = wrap(
        AddCards.setupButtons, add_query_button, "before")


def setup_options_menu():
    # add options submenu to Tools menu
    action = QAction(app_icon, "WordQuery...", mw)
    action.triggered.connect(show_options_dlg)
    mw.form.menuTools.addAction(action)
    global have_setup
    have_setup = True


# def start_here():
#     # config.read()
#     if not have_setup:
#         setup_options_menu()
#         customize_addcards()
#         setup_browser_menu()
#         setup_context_menu()
#     # wquery.start_services()


# addHook("profileLoaded", start_here)

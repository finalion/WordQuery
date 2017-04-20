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

from anki.hooks import addHook

############## other config here ##################
# update all fields ignoring the original field content
update_all = False
# shortcut
shortcut = 'Ctrl+Q'
###################################################


def start_here():
    import wquery
    wquery.config.read()
    if not wquery.have_setup:
        wquery.setup_options_menu()
        wquery.customize_addcards()
        wquery.setup_browser_menu()
        wquery.setup_context_menu()
    wquery.start_services()
    wquery.set_shortcut(shortcut)

addHook("profileLoaded", start_here)

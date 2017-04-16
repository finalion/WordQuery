#-*- coding:utf-8 -*-
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

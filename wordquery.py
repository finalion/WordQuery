#-*- coding:utf-8 -*-
from anki.hooks import addHook
# update all fields?
update_all = False


def start_here():
    import wquery
    wquery.config.read()
    if not wquery.have_setup:
        wquery.setup_options_menu()
        wquery.customize_addcards()
        wquery.setup_browser_menu()
        wquery.setup_context_menu()
    wquery.start_services()

addHook("profileLoaded", start_here)

#-*- coding:utf-8 -*-
import wquery
from wquery import context as c

wquery.read_parameters()
# showInfo(str(c.maps) + str(c.model_name))

wquery.setup_options_menu()
wquery.customize_addcards()
wquery.setup_browser_menu()
wquery.setup_context_menu()

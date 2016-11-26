#-*- coding:utf-8 -*-
import os
import sys
from collections import defaultdict
savepath = os.path.join(sys.path[0], 'config')

focus_editor = None
focus_browser = None
focus_note = None
maps = list()
model_id = -10000
# [model_id: maps]
mappings = defaultdict(list)

update_all = False


def update_maps():
    global model_id, maps
    model_id = focus_editor.model()['id']
    maps = mappings[model_id]

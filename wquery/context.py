#-*- coding:utf-8 -*-
import os
from collections import defaultdict

cfgpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wqcfg')

maps = list()
last_model_id = -10000
# [model_id: maps]
mappings = defaultdict(list)

update_all = False

context = defaultdict(int)
# online dictionary cache to avoid duplicate query

def get_maps(id):
    return mappings[id]
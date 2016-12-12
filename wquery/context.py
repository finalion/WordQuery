#-*- coding:utf-8 -*-
import os
from collections import defaultdict

maps = list()
last_model_id = -1000
# [model_id: maps]
mappings = defaultdict(list)

update_all = False

context = defaultdict(int)


def get_cfgpath(mw):
    cfgpath = os.path.join(os.path.dirname(
        os.path.realpath(__file__)), '%s.wqcfg' % mw.pm.name)
    return cfgpath


def get_maps(id):
    return mappings[id]

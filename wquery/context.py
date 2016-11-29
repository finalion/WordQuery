#-*- coding:utf-8 -*-
import os
import sys
from collections import defaultdict
savepath = os.path.join(sys.path[0], 'config')

maps = list()
model_id = -10000
# [model_id: maps]
mappings = defaultdict(list)

update_all = False

context = defaultdict(int)
# online dictionary cache to avoid duplicate query
online_cache = defaultdict(str)

available_online_fields = ['phonetic', 'explains', 'web-explains']

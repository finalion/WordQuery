#-*- coding:utf-8 -*-
import os
from collections import defaultdict

cfgpath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'wqcfg')

maps = list()
model_id = -10000
# [model_id: maps]
mappings = defaultdict(list)

update_all = False

context = defaultdict(int)
# online dictionary cache to avoid duplicate query
online_cache = defaultdict(str)

available_youdao_fields = {'eng': {
    u'有道·音标': 'phonetic', u'有道·基本释义': 'explains', u'有道·柯林斯英汉': 'collins', u'有道·21世纪': 'ec21',
    u'有道·英英释义': 'ee', u'有道·网络释义': 'web_trans', u'有道·同根词': 'rel_word', u'有道·同近义词': 'syno',
    u'有道·双语例句': 'blng_sents_part', u'有道·原生例句': 'media_sents_part', u'有道·权威例句': 'auth_sents_part',
    u'有道·百科': 'baike', u'有道·新英汉大辞典(中)': 'ce_new', u'有道·汉语词典(中)': 'hh', u'有道·专业释义(中)': 'special'
},
    'fr': {
    u'有道·基本释义': 'explains', u'有道·英英释义': 'ee', u'有道·网络释义': 'web_trans', u'有道·双语例句': 'blng_sents_part',
    u'有道·汉语词典(中)': 'hh', u'有道·百科': 'baike'
},
    'jap': {
    u'有道·基本释义': 'explains', u'有道·网络释义': 'web_trans', u'有道·双语例句': 'blng_sents_part', u'有道·百科': 'baike',
    u'有道·汉语词典(中)': 'hh'
},
    'ko': {
    u'有道·基本释义': 'explains', u'有道·网络释义': 'web_trans', u'有道·双语例句': 'blng_sents_part', u'有道·百科': 'baike',
    u'有道·汉语词典(中)': 'hh'
}
}

lang = 'eng'

#-*- coding:utf-8 -*-
from anki.lang import currentLang
trans = {

    'CHECK_FILENAME_LABEL': {'zh_CN': u'使用文件名作为标签', 'en': 'Use filename as dict label'},
    'EXPORT_MEDIA': {'zh_CN': u'导出媒体文件', 'en': 'Export media files'},
    'DICTS_FOLDERS': {'zh_CN': u'字典文件夹', 'en': 'Dict folders'},
    'CHOOSE_NOTE_TYPES': {'zh_CN': u'选择笔记类型', 'en': 'Choose note types'},
    'CURRENT_NOTE_TYPE': {'zh_CN': u'当前类型', 'en': 'Current type'},
    'MDX_SERVER': {'zh_CN': u'MDX服务器', 'en': 'MDX server'},
    'USE_DICTIONARY': {'zh_CN': u'使用字典', 'en': 'Use dict'},
    'UPDATED': {'zh_CN': u'更新', 'en': 'Updated'},
    'CARDS': {'zh_CN': u'卡片', 'en': 'cards'},
    'QUERIED': {'zh_CN': u'查询', 'en': 'Queried'},
    'FIELDS': {'zh_CN': u'字段', 'en': 'Fields'},
    'WORDS': {'zh_CN': u'单词', 'en': 'Words'},
    'NOT_DICT_FIELD': {'zh_CN': u'不是字典字段', 'en': 'Not dict field'},
    'NOTE_TYPE_FIELDS': {'zh_CN': u'<b>笔记字段</b>', 'en': '<b>Note fields</b>'},
    'DICTS': {'zh_CN': u'<b>字典</b>', 'en': '<b>Dict</b>'},
    'DICT_FIELDS': {'zh_CN': u'<b>字典字段</b>', 'en': '<b>Dict fields</b>'},
    'RADIOS_DESC': {'zh_CN': u'<b>单选框选中为待查询单词字段</b>', 'en': '<b>Word field needs to be selected.</b>'},
}


def _(key):
    lang = 'zh_CN' if currentLang == 'zh_CN' else 'en'
    return trans[key][lang]

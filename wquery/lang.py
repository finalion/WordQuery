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

from anki.lang import currentLang
trans = {
    'CHECK_FILENAME_LABEL': {'zh_CN': u'使用文件名作为标签', 'en': u'Use filename as dict label', 'fr': r"Utiliser le nom de fichier en tant qu'étiquette de dico"},
    'EXPORT_MEDIA': {'zh_CN': u'导出媒体文件', 'en': u'Export media files', 'fr': u'Exporter les fichiers multimédias'},
    'DICTS_FOLDERS': {'zh_CN': u'字典文件夹', 'en': u'Dict folders', 'fr': u'Dossiers dico'},
    'CHOOSE_NOTE_TYPES': {'zh_CN': u'选择笔记类型', 'en': u'Choose note types', 'fr': u'Choisir le type de note '},
    'CURRENT_NOTE_TYPE': {'zh_CN': u'当前类型', 'en': u'Current type', 'fr': u'Type utilisé en cours'},
    'MDX_SERVER': {'zh_CN': u'MDX服务器', 'en': u'MDX server', 'fr': u'serveur MDX'},
    'USE_DICTIONARY': {'zh_CN': u'使用字典', 'en': u'Use dict', 'fr': u'Utilisé un dico'},
    'UPDATED': {'zh_CN': u'更新', 'en': u'Updated', 'fr': u'Mettre à jour'},
    'CARDS': {'zh_CN': u'卡片', 'en': u'Cards', 'fr': u'Cartes'},
    'QUERIED': {'zh_CN': u'查询', 'en': u'Queried', 'fr': u'Quêté'},
    'FIELDS': {'zh_CN': u'字段', 'en': u'Fields', 'fr': u'Champs'},
    'WORDS': {'zh_CN': u'单词', 'en': u'Words', 'fr': u'Mots'},
    'NOT_DICT_FIELD': {'zh_CN': u'不是字典字段', 'en': u'Not dict field', 'fr': u'Pas un champ de dico'},
    'NOTE_TYPE_FIELDS': {'zh_CN': u'<b>笔记字段</b>', 'en': u'<b>Note fields</b>', 'fr': u'<b>Champ de note</b>'},
    'DICTS': {'zh_CN': u'<b>字典</b>', 'en': u'<b>Dict</b>', 'fr': u'<b>Dico</b>'},
    'DICT_FIELDS': {'zh_CN': u'<b>字典字段</b>', 'en': u'<b>Dict fields</b>', 'fr': u'<b>Champ de dico</b>'},
    'RADIOS_DESC': {'zh_CN': u'<b>单选框选中为待查询单词字段</b>', 'en': u'<b>Word field needs to be selected.</b>', 'fr': u'<b>Champ de mot doit être sélectionné. </b>'},
    'NO_QUERY_WORD': {'zh_CN': u'查询字段无单词', 'en': u'No word is found in the query field', 'fr': u'Aucun est trouvée dans le champ'}
}


def _(key, lang=currentLang):
    if lang != 'zh_CN' and lang != 'en' and lang != 'fr':
        lang = 'en'  # fallback
    return trans[key][lang]


def _sl(key):
    return trans[key].values()

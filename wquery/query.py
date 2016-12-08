#-*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import os
import urlparse
import re
import json
import xml
import urllib
import urllib2
import aqt
from aqt import mw
from aqt.qt import *
from aqt.utils import shortcut, showInfo, showText, tooltip
# import trackback
from mdict.mdict_query import IndexBuilder
from collections import defaultdict
import wquery.context as c
import sqlite3
from .service import find_service
index_builders = defaultdict(int)


class MdxIndexer(QThread):

    def __init__(self, ix):
        QThread.__init__(self)
        self.ix = ix

    def run(self):
        global index_builders
        if self.ix == -1:
            # index all dicts
            for i, each in enumerate(c.maps):
                if each['checked'] and each["dict"]:
                    index_builders[i] = self.work(each["dict"])
        else:
            # only index given dict, specified by ix
            index_builders[self.ix] = self.work(c.maps[self.ix]["dict"])

    def work(self, dict_path):
        # showInfo("%d, %s" % (self.ix, dict_path))
        if not dict_path.startswith("http://") and os.path.isabs(dict_path):
            index_builder = IndexBuilder(dict_path)
            errors, styles = save_media_files(index_builder, '*.css', '*.js')
            # if '*.css' in errors:
            # info = ' '.join([each[2:] for each in ['*.css', '*.js'] if
            # each in errors ])
            # tooltip(u"%s字典中缺失css文件，格式显示可能不正确，请自行查找文件并放入媒体文件夹中" %
            #         (dict_path), period=3000)
            return index_builder


def index_mdx(ix=-1):
    mw.progress.start(immediate=True, label="Index building...")
    index_thread = MdxIndexer(ix)
    index_thread.start()
    while not index_thread.isFinished():
        mw.app.processEvents()
        index_thread.wait(100)
    mw.progress.finish()


def query_from_menu():
    browser = c.context['browser']
    if not browser:
        return
    notes = [browser.mw.col.getNote(note_id)
             for note_id in browser.selectedNotes()]
    if len(notes) == 0:
        return
    if len(notes) == 1:
        c.context['editor'] = browser.editor
        query_from_editor()
    if len(notes) > 1:
        mw.progress.start(immediate=True, label="Querying...")
        for i, note in enumerate(notes):
            word = note.fields[0]
            c.model_id = note.model()['id']
            c.maps = c.mappings[c.model_id]
            for j, res in query_all_flds(word):
                if res == "":
                    if c.update_all:
                        note.fields[j] = res
                else:
                    note.fields[j] = res
                note.flush()
            mw.progress.update(label="Queried %d words..." % (i + 1))
        browser.model.reset()
        mw.progress.finish()
        # browser.model.reset()
        # browser.endReset()
        tooltip(u'共更新 %d 张卡片' % len(notes))


def purify_word(word):
    m = re.search('\s*[a-zA-Z]+[a-zA-Z -]*', word)
    if m:
        return m.group().strip()
    return ""


def query_from_editor():
    editor = c.context['editor']
    if not editor:
        return
    c.model_id = editor.note.model()['id']
    word = editor.note.fields[0].decode('utf-8')
    # showInfo(word.decode('utf-8'))
    c.maps = c.mappings[c.model_id]
    mw.progress.start(immediate=True, label="Querying...")
    for i, res in query_all_flds(word):
        if res == "":
            if c.update_all:
                editor.note.fields[i] = res
        else:
            editor.note.fields[i] = res
    # editor.note.flush()
    mw.progress.finish()
    editor.setNote(editor.note, focus=True)
    editor.saveNow()


def query_all_flds(word):
    purified_word = purify_word(word)
    for i, each in enumerate(c.maps):
        res = ""
        if i == 0:
            res = word
        else:
            if each['checked'] and each['dict'].strip():
                res = query_mdict(purified_word, i, **each)
        yield i, res


def query_mdict(word, ix, **kwargs):
    dict_path = kwargs.get('dict', '').strip()
    dict_field = kwargs.get('dict_field', '').strip()
    lang = kwargs.get('youdao', 'eng').strip()
    if dict_path.startswith("http://"):
        dict_path = dict_path + \
            '/' if not dict_path.endswith('/') else dict_path
        try:
            req = urllib2.urlopen(dict_path + word)
            return update_dict_field(ix, req.read(), url=dict_path)
        except:
            return ""
    # elif dict_path.startswith(u"有道·"):
    #     fld = c.available_youdao_fields[lang].get(dict_path, None)
    #     return query_youdao(word, lang, fld)
    elif os.path.isabs(dict_path):
        if not index_builders[ix]:
            index_mdx(ix)
        result = index_builders[ix].mdx_lookup(word)
        if result:
            return update_dict_field(ix, result[0], index_builder=index_builders[ix])
        return ""
    else:
        service = find_service(dict_path)
        if service:
            result = service['instance'].active(dict_field, word)
            # showInfo(result)
            return result


def update_dict_field(idx, text, **kwargs):
    url = kwargs.get('url', '')
    index_builder = kwargs.get('index_builder', 0)
    if url:
        return convert_media_path(text, url)
    if index_builder:
        return convert_media_path(text, index_builder)


def save_media_files(ib, *args, **kwargs):
    """
    get the necessary static files from local mdx dictionary
    ** kwargs: data = list
    """
    lst = []
    errors = []
    styles = []
    wild = list(args) + ['*' + os.path.basename(each)
                         for each in kwargs.get('data', [])]
    try:
        for each in wild:
            keys = ib.get_mdd_keys(each)
            if not keys:
                errors.append(each)
            lst.extend(keys)
        # showInfo(str(errors))
        for each in lst:
            try:
                bytes_list = ib.mdd_lookup(each)
                if bytes_list:
                    savepath = os.path.join(
                        mw.col.media.dir(), '_' + os.path.basename(each))
                    if os.path.basename(each).endswith('.css') or os.path.basename(each).endswith('.js'):
                        styles.append(os.path.basename(each))
                    if not os.path.exists(savepath):
                        with open(savepath, 'wb') as f:
                            f.write(bytes_list[0])
            except sqlite3.OperationalError as e:
                showInfo(str(e))
        # showInfo(str(styles))
    except AttributeError:
        '''
        有些字典会出这样的错误u AttributeError: 'IndexBuilder' object has no attribute '_mdd_db'
        '''
        pass
    return errors, styles


def download_media_files(html, url, *args, **kwargs):
    errors, styles = list(), list()
    for each in kwargs.get('data', []):
        abs_url = urlparse.urljoin(url, each)
        savepath = os.path.join(
            mw.col.media.dir(), '_' + os.path.basename(each))
        if os.path.basename(each).endswith('.css') or os.path.basename(each).endswith('.js'):
            styles.append(os.path.basename(each))
        if not os.path.exists(savepath):
            try:
                urllib.urlretrieve(abs_url, savepath)
            except:
                errors.append(each)
    return errors, styles


def convert_media_path(html, key):
    """
    convert the media path to actual path in anki's collection media folder.'
    """
    lst = list()
    mcss = re.findall('href="(\S+?\.css)"', html)
    lst.extend(list(set(mcss)))
    mjs = re.findall('src="([\w\./]\S+?\.js)"', html)
    lst.extend(list(set(mjs)))
    msrc = re.findall('<img.*?src="([\w\./]\S+?)".*?>', html)
    lst.extend(list(set(msrc)))
    if isinstance(key, IndexBuilder):
        errors, styles = save_media_files(key, data=list(set(lst)))
    else:
        errors, styles = download_media_files(html, key, data=list(set(lst)))

    newlist = ['_' + each.split('/')[-1] for each in lst]
    # print newlist
    for each in zip(lst, newlist):
        html = html.replace(each[0], each[1])
    html = '<br>'.join(["<style>@import url('_%s');</style>" %
                        style for style in styles if style.endswith('.css')]) + html
    html += '<br>'.join(['<script type="text/javascript" src="_%s"></script>' %
                         style for style in styles if style.endswith('.js')])
    return unicode(html)

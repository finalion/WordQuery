#-*- coding:utf-8 -*-
import os
import re
import urllib
import urlparse
from collections import defaultdict

import aqt
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo, showText
from mdict.mdict_query import IndexBuilder

from .base import Service, export, with_styles, QueryResult


class MdxService(Service):
    __register_label__ = u'本地Mdx词典'

    def __init__(self):
        Service.__init__(self)
        # cache all the static files queried, cache index_builder
        # key: dict_path
        # value: {'builder':index_builder, 'files':[...static files list...]}
        self.cache = defaultdict(lambda: defaultdict(set))

    def index(self):
        mw.progress.start(immediate=True, label="Index building...")
        index_builder = IndexBuilder(self.dict_path)
        # if '*.css' in errors:
        # info = ' '.join([each[2:] for each in ['*.css', '*.js'] if
        # each in errors ])
        # tooltip(u"%s字典中缺失css文件，格式显示可能不正确，请自行查找文件并放入媒体文件夹中" %
        #         (dict_path), period=3000)
        mw.progress.finish()
        return index_builder

    def active(self, dict_path, word):
        self.word = word
        self.dict_path = dict_path
        self.index_builder = self.cache[dict_path]['builder']
        if not self.index_builder:
            self.index_builder = self.index()
            self.cache[dict_path]['builder'] = self.index_builder
        result = self.index_builder.mdx_lookup(word)
        if result:
            ss = self.adapt_to_anki(result[0])
            # open('d:\\wmu.html', 'wb').write(ss)
            return QueryResult(result=ss[0], js=ss[1])
        return self.default_result

    def adapt_to_anki(self, html):
        """
        1. convert the media path to actual path in anki's collection media folder.
        2. remove the js codes (js inside will expires.)
        3. import css, to make sure the css file can be synced. TO VALIDATE!
        """
        # convert media path, save media files
        media_files_set = set()
        mcss = re.findall('href="(\S+?\.css)"', html)
        media_files_set.update(set(mcss))
        mjs = re.findall('src="([\w\./]\S+?\.js)"', html)
        media_files_set.update(set(mjs))
        msrc = re.findall('<img.*?src="([\w\./]\S+?)".*?>', html)
        media_files_set.update(set(msrc))
        for each in media_files_set:
            html = html.replace(each, '_' + each.split('/')[-1])
        errors, styles = self.save_media_files(media_files_set)
        # import css
        html = '<br>'.join(["<style>@import url('%s');</style>" %
                            style for style in styles if style.endswith('.css')]) + html
        # remove the js codes, send them back to the editor and add them to the template
        # 插入笔记<div>中不能有js代码，否则会不显示。例如mwu字典
        js = re.findall('<script.*?>.*?</script>', html, re.DOTALL)
        # for each in js:
        #     html = html.replace(each, '')
        return unicode(html), '\n'.join(js)

    def save_media_files(self, data):
        """
        get the necessary static files from local mdx dictionary
        ** kwargs: data = list
        """
        diff = data.difference(self.cache[self.dict_path]['files'])
        self.cache[self.dict_path]['files'].update(diff)
        lst, errors, styles = list(), list(), list()
        wild = ['*' + os.path.basename(each) for each in diff]
        try:
            for each in wild:
                keys = self.index_builder.get_mdd_keys(each)
                if not keys:
                    errors.append(each)
                lst.extend(keys)
            # showInfo(str(errors))
            for each in lst:
                try:
                    bytes_list = self.index_builder.mdd_lookup(each)
                    if bytes_list:
                        savepath = os.path.join(
                            mw.col.media.dir(), '_' + os.path.basename(each))
                        if os.path.basename(each).endswith('.css') or os.path.basename(each).endswith('.js'):
                            styles.append('_' + os.path.basename(each))
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

#-*- coding:utf-8 -*-
import os
import re
import urllib
import urlparse
from collections import defaultdict

import aqt
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from mdict.mdict_query import IndexBuilder

from .base import Service, export


class MdxIndexer(QThread):

    def __init__(self, dict_path, index_builders):
        QThread.__init__(self)
        self.dict_path = dict_path
        self.index_builders = index_builders

    def run(self):
        index_builder = IndexBuilder(dict_path)
        errors, styles = save_media_files(index_builder, '*.css', '*.js')
        # if '*.css' in errors:
        # info = ' '.join([each[2:] for each in ['*.css', '*.js'] if
        # each in errors ])
        # tooltip(u"%s字典中缺失css文件，格式显示可能不正确，请自行查找文件并放入媒体文件夹中" %
        #         (dict_path), period=3000)
        self.index_builders[self.dict_path] = index_builder


class MdxService(Service):
    __register_label__ = u'本地Mdx词典'

    def __init__(self):
        Service.__init__(self)
        self.index_builders = defaultdict(int)

    def index(self):
        mw.progress.start(immediate=True, label="Index building...")
        index_builder = IndexBuilder(self.dict_path)
        errors, styles = self.save_media_files(index_builder, '*.css', '*.js')
        # if '*.css' in errors:
        # info = ' '.join([each[2:] for each in ['*.css', '*.js'] if
        # each in errors ])
        # tooltip(u"%s字典中缺失css文件，格式显示可能不正确，请自行查找文件并放入媒体文件夹中" %
        #         (dict_path), period=3000)
        self.index_builders[self.dict_path] = index_builder
        mw.progress.finish()
# @export('完整释义', 0)

    def active(self, dict_path, word):
        self.word = word
        self.dict_path = dict_path
        if not self.index_builders[dict_path]:
            self.index()
        result = self.index_builders[dict_path].mdx_lookup(word)
        if result:
            ss = self.convert_media_path(result[0])
            return ss
        return ""

    def convert_media_path(self, html):
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

        errors, styles = self.save_media_files(data=list(set(lst)))

        newlist = ['_' + each.split('/')[-1] for each in lst]
        # print newlist
        for each in zip(lst, newlist):
            html = html.replace(each[0], each[1])
        html = '<br>'.join(["<style>@import url('_%s');</style>" %
                            style for style in styles if style.endswith('.css')]) + html
        html += '<br>'.join(['<script type="text/javascript" src="_%s"></script>' %
                             style for style in styles if style.endswith('.js')])
        return unicode(html)

    def save_media_files(self, *args, **kwargs):
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
                keys = self.index_builders[
                    self.dict_path].get_mdd_keys(each)
                if not keys:
                    errors.append(each)
                lst.extend(keys)
            # showInfo(str(errors))
            for each in lst:
                try:
                    bytes_list = self.index_builders[
                        self.dict_path].mdd_lookup(each)
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

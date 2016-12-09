#-*- coding:utf-8 -*-
import os
import re
import urllib
import urllib2
import urlparse
from collections import defaultdict

import aqt
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from mdict.mdict_query import IndexBuilder

from .base import Service, export


class RemoteMdxService(Service):
    __register_label__ = u'Mdx服务器'

    def __init__(self):
        Service.__init__(self)

    def active(self, dict_path, word):
        self.word = word
        self.url = dict_path + '/' if not dict_path.endswith('/') else dict_path
        try:
            req = urllib2.urlopen(self.url + word)
            return self.convert_media_path(req.read())
        except:
            return ""

    def download_media_files(self, html,  *args, **kwargs):
        errors, styles = list(), list()
        for each in kwargs.get('data', []):
            abs_url = urlparse.urljoin(self.url, each)
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

        errors, styles = self.download_media_files(html, data=list(set(lst)))

        newlist = ['_' + each.split('/')[-1] for each in lst]
        # print newlist
        for each in zip(lst, newlist):
            html = html.replace(each[0], each[1])
        html = '<br>'.join(["<style>@import url('_%s');</style>" %
                            style for style in styles if style.endswith('.css')]) + html
        html += '<br>'.join(['<script type="text/javascript" src="_%s"></script>' %
                             style for style in styles if style.endswith('.js')])
        return unicode(html)

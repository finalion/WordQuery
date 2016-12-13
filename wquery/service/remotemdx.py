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
from aqt.utils import showInfo, showText
from mdict.mdict_query import IndexBuilder

from .base import Service, export, QueryResult


class RemoteMdxService(Service):
    __register_label__ = u'Mdx服务器'

    def __init__(self):
        Service.__init__(self)
        # key: url
        # value: set of static files
        self.cache = defaultdict(set)

    def active(self, dict_path, word):
        self.word = word
        self.url = dict_path + \
            '/' if not dict_path.endswith('/') else dict_path
        try:
            req = urllib2.urlopen(self.url + word)
            result, js = self.adapt_to_anki(req.read())
            return QueryResult(result=result, js=js)
        except:
            return self.default_result

    def download_media_files(self, data):
        diff = data.difference(self.cache[self.url])
        self.cache[self.url].update(diff)
        errors, styles = list(), list()
        for each in diff:
            abs_url = urlparse.urljoin(self.url, each)
            savepath = os.path.join(
                mw.col.media.dir(), '_' + os.path.basename(each))
            if os.path.basename(each).endswith('.css') or os.path.basename(each).endswith('.js'):
                styles.append('_' + os.path.basename(each))
            if not os.path.exists(savepath):
                try:
                    urllib.urlretrieve(abs_url, savepath)
                except:
                    errors.append(each)
        return errors, styles

    def adapt_to_anki(self, html):
        """
        1. convert the media path to actual path in anki's collection media folder.
        2. remove the js codes
        3. import css, to make sure the css file can be synced. TO VALIDATE!
        """
        media_files_set = set()
        mcss = re.findall('href="(\S+?\.css)"', html)
        media_files_set.update(set(mcss))
        mjs = re.findall('src="([\w\./]\S+?\.js)"', html)
        media_files_set.update(set(mjs))
        msrc = re.findall('<img.*?src="([\w\./]\S+?)".*?>', html)
        media_files_set.update(set(msrc))
        for each in media_files_set:
            html = html.replace(each, '_' + each.split('/')[-1])
        errors, styles = self.download_media_files(media_files_set)
        html = '<br>'.join(["<style>@import url('%s');</style>" %
                            style for style in styles if style.endswith('.css')]) + html
        js = re.findall('<script.*?>.*?</script>', html, re.DOTALL)
        # for each in js:
        #     html = html.replace(each, '')
        # showText(html)
        return unicode(html), '\n'.join(js)

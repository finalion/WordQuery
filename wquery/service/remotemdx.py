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

import os
# import ntpath
import re
import urllib
import urllib2
import urlparse
from collections import defaultdict

import aqt
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo, showText

from .base import QueryResult, WebService, export, with_styles, register


@register(u'MDX server')
class RemoteMdx(WebService):

    def __init__(self):
        super(RemoteMdx, self).__init__()
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
            return QueryResult.default()

    def download_media_files(self, data):
        diff = data.difference(self.cache[self.url])
        self.cache[self.url].update(diff)
        errors, styles = list(), list()
        for each in diff:
            basename = os.path.basename(each.replace('\\', os.path.sep))
            saved_basename = '_' + basename
            abs_url = urlparse.urljoin(self.url, each)
            if basename.endswith('.css') or basename.endswith('.js'):
                styles.append(saved_basename)
            if not os.path.exists(saved_basename):
                try:
                    urllib.urlretrieve(abs_url, saved_basename)
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
        mcss = re.findall(r'href="(\S+?\.css)"', html)
        media_files_set.update(set(mcss))
        mjs = re.findall(r'src="([\w\./]\S+?\.js)"', html)
        media_files_set.update(set(mjs))
        msrc = re.findall(r'<img.*?src="([\w\./]\S+?)".*?>', html)
        media_files_set.update(set(msrc))
        for each in media_files_set:
            html = html.replace(each, '_' + each.split('/')[-1])
        errors, styles = self.download_media_files(media_files_set)
        html = u'<br>'.join([u"<style>@import url('%s');</style>".format(style)
                             for style in styles if style.endswith('.css')]) + html
        js = re.findall(r'<script.*?>.*?</script>', html, re.DOTALL)
        # for each in js:
        #     html = html.replace(each, '')
        # showText(html)
        return unicode(html), u'\n'.join(js)

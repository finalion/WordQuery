# -*- coding:utf-8 -*-
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

import inspect
import os
# use ntpath module to ensure the windows-style (e.g. '\\LDOCE.css')
# path can be processed on Unix platform.
# However, anki version on mac platforms doesn't including this package?
# import ntpath
import re
import shutil
import sqlite3
import urllib

try:
    import urllib2
except:
    import urllib.request as urllib2
import zlib
from collections import defaultdict
from functools import wraps

try:
    from cookielib import CookieJar
except:
    from http.cookiejar import CookieJar
from aqt import mw
from aqt.qt import QFileDialog
from aqt.utils import showInfo, showText
from ..context import config
from ..libs import MdxBuilder, StardictBuilder
from ..utils import MapDict, wrap_css
import requests


def register(label):
    """register the dict service with a label, which will be shown in the dicts list."""

    def _deco(cls):
        cls.__register_label__ = label
        return cls

    return _deco


def export(label, index):
    """export dict field function with a label, which will be shown in the fields list."""

    def _with(fld_func):
        @wraps(fld_func)
        def _deco(cls, *args, **kwargs):
            res = fld_func(cls, *args, **kwargs)
            return QueryResult(result=res) if not isinstance(res, QueryResult) else res

        _deco.__export_attrs__ = (label, index)
        return _deco

    return _with


def copy_static_file(filename, new_filename=None, static_dir='static'):
    """
    copy file in static directory to media folder
    """
    abspath = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           static_dir,
                           filename)
    shutil.copy(abspath, new_filename if new_filename else filename)


def with_styles(**styles):
    """
    cssfile: specify the css file in static folder
    css: css strings
    js: js strings
    jsfile: specify the js file in static folder
    """

    def _with(fld_func):
        @wraps(fld_func)
        def _deco(cls, *args, **kwargs):
            res = fld_func(cls, *args, **kwargs)
            cssfile, css, jsfile, js, need_wrap_css, class_wrapper = \
                styles.get('cssfile', None), \
                styles.get('css', None), \
                styles.get('jsfile', None), \
                styles.get('js', None), \
                styles.get('need_wrap_css', False), \
                styles.get('wrap_class', '')

            def wrap(html, css_obj, is_file=True):
                # wrap css and html
                if need_wrap_css and class_wrapper:
                    html = u'<div class="{}">{}</div>'.format(
                        class_wrapper, html)
                    return html, wrap_css(css_obj, is_file=is_file, class_wrapper=class_wrapper)[0]
                return html, css_obj

            if cssfile:
                new_cssfile = cssfile if cssfile.startswith('_') \
                    else u'_' + cssfile
                # copy the css file to media folder
                copy_static_file(cssfile, new_cssfile)
                # wrap the css file
                res, new_cssfile = wrap(res, new_cssfile)
                res = u'<link type="text/css" rel="stylesheet" href="{0}" />{1}'.format(
                    new_cssfile, res)
            if css:
                res, css = wrap(res, css, is_file=False)
                res = u'<style>{0}</style>{1}'.format(css, res)

            if not isinstance(res, QueryResult):
                return QueryResult(result=res, jsfile=jsfile, js=js)
            else:
                res.set_styles(jsfile=jsfile, js=js)
                return res

        return _deco

    return _with


class Service(object):
    '''service base class'''

    def __init__(self):
        self._exporters = self.get_exporters()
        self._fields, self._actions = zip(*self._exporters) \
            if self._exporters else (None, None)
        # query interval: default 500ms
        self.query_interval = 0.5

    @property
    def fields(self):
        return self._fields

    @property
    def actions(self):
        return self._actions

    @property
    def exporters(self):
        return self._exporters

    def get_exporters(self):
        flds = dict()
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for method in methods:
            export_attrs = getattr(method[1], '__export_attrs__', None)
            if export_attrs:
                label, index = export_attrs
                flds.update({int(index): (label, method[1])})
        sorted_flds = sorted(flds)
        return [flds[key] for key in sorted_flds]

    def active(self, action_label, word):
        self.word = word
        # if the service instance is LocalService,
        # then have to build then index.
        if isinstance(self, LocalService):
            self.notify(MapDict(type='text', index=self.work_id,
                                text=u'Building %s...' % self._filename))
            if isinstance(self, MdxService) or isinstance(self, StardictService):
                self.builder.check_build()

        for each in self.exporters:
            if action_label == each[0]:
                self.notify(MapDict(type='info', index=self.work_id,
                                    service_name=self.title,
                                    field_name=action_label,
                                    flag=u'->'))
                result = each[1]()
                self.notify(MapDict(type='info', index=self.work_id,
                                    service_name=self.title,
                                    field_name=action_label,
                                    flag=u'√'))
                return result
        return QueryResult.default()

    def set_notifier(self, progress_update, index):
        self.notify_signal = progress_update
        self.work_id = index

    def notify(self, data):
        self.notify_signal.emit(data)

    @staticmethod
    def get_anki_label(filename, type_):
        formats = {'audio': u'[sound:{0}]',
                   'img': u'<img src="{0}">',
                   'video': u'<video controls="controls" width="100%" height="auto" src="{0}"></video>'}
        return formats[type_].format(filename)


class WebService(Service):
    '''web service class'''

    def __init__(self):
        super(WebService, self).__init__()
        self.cache = defaultdict(defaultdict)
        self._cookie = CookieJar()
        self._opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self._cookie))
        self.query_interval = 1

    def cache_this(self, result):
        self.cache[self.word].update(result)
        return result

    def cached(self, key):
        return (self.word in self.cache) and (key in self.cache[self.word])

    def cache_result(self, key):
        return self.cache[self.word].get(key, u'')

    @property
    def title(self):
        return self.__register_label__

    @property
    def unique(self):
        return self.__class__.__name__

    def get_response(self, url, data=None, headers=None, timeout=10):
        default_headers = {'User-Agent': 'Anki WordQuery',
                           'Accept-Encoding': 'gzip'}
        if headers:
            default_headers.update(headers)

        request = urllib2.Request(url, headers=default_headers)
        try:
            response = self._opener.open(request, data=data, timeout=timeout)
            data = response.read()    # return bytes
            if response.info().get('Content-Encoding') == 'gzip':
                data = zlib.decompress(data, 16 + zlib.MAX_WBITS)   # return bytes
            return data.decode('utf-8')  # TODO: all data can be decoded by utf-8??
        except:
            return ''

    @classmethod
    def download(cls, url, filename):
        try:
            return urllib.urlretrieve(url, filename)
        except AttributeError:
            try:
                with open(filename, "wb") as f:
                    f.write(requests.get(url).content)
                return True
            except Exception as e:
                pass
        except Exception as e:
            pass


class LocalService(Service):

    def __init__(self, dict_path):
        super(LocalService, self).__init__()
        self.dict_path = dict_path
        self.builder = None
        self.missed_css = set()

    @property
    def unique(self):
        return self.dict_path

    @property
    def title(self):
        return self.__register_label__

    @property
    def _filename(self):
        return os.path.splitext(os.path.basename(self.dict_path))[0]


class MdxService(LocalService):

    def __init__(self, dict_path):
        super(MdxService, self).__init__(dict_path)
        self.media_cache = defaultdict(set)
        self.cache = defaultdict(str)
        self.query_interval = 0.01
        self.styles = []
        self.builder = MdxBuilder(dict_path)
        self.builder.get_header()

    @staticmethod
    def support(dict_path):
        return os.path.isfile(dict_path) and dict_path.lower().endswith('.mdx')

    @property
    def title(self):
        if config.use_filename or not self.builder._title or self.builder._title.startswith('Title'):
            return self._filename
        else:
            return self.builder.meta['title']

    @export(u"default", 0)
    def fld_whole(self):
        html = self.get_html()
        js = re.findall(r'<script.*?>.*?</script>', html, re.DOTALL)
        return QueryResult(result=html, js=u'\n'.join(js))

    def get_html(self):
        if not self.cache[self.word]:
            html = ''
            result = self.builder.mdx_lookup(self.word)  # self.word: unicode
            if result:
                if result[0].upper().find(u"@@@LINK=") > -1:
                    # redirect to a new word behind the equal symol.
                    self.word = result[0][len(u"@@@LINK="):].strip()
                    return self.get_html()
                else:
                    html = self.adapt_to_anki(result[0])
                    self.cache[self.word] = html
        return self.cache[self.word]

    def adapt_to_anki(self, html):
        """
        1. convert the media path to actual path in anki's collection media folder.
        2. remove the js codes (js inside will expires.)
        """
        # convert media path, save media files
        media_files_set = set()
        mcss = re.findall(r'href="(\S+?\.css)"', html)
        media_files_set.update(set(mcss))
        mjs = re.findall(r'src="([\w\./]\S+?\.js)"', html)
        media_files_set.update(set(mjs))
        msrc = re.findall(r'<img.*?src="([\w\./]\S+?)".*?>', html)
        media_files_set.update(set(msrc))
        msound = re.findall(r'href="sound:(.*?\.(?:mp3|wav))"', html)
        if config.export_media:
            media_files_set.update(set(msound))
        for each in media_files_set:
            html = html.replace(each, u'_' + each.split('/')[-1])
        # find sounds
        p = re.compile(
            r'<a[^>]+?href=\"(sound:_.*?\.(?:mp3|wav))\"[^>]*?>(.*?)</a>')
        html = p.sub(u"[\\1]\\2", html)
        self.save_media_files(media_files_set)
        for cssfile in mcss:
            cssfile = '_' + \
                      os.path.basename(cssfile.replace('\\', os.path.sep))
            # if not exists the css file, the user can place the file to media
            # folder first, and it will also execute the wrap process to generate
            # the desired file.
            if not os.path.exists(cssfile):
                self.missed_css.add(cssfile[1:])
            new_css_file, wrap_class_name = wrap_css(cssfile)
            html = html.replace(cssfile, new_css_file)
            # add global div to the result html
            html = u'<div class="{0}">{1}</div>'.format(
                wrap_class_name, html)

        return html

    def save_file(self, filepath_in_mdx, savepath=None):
        basename = os.path.basename(filepath_in_mdx.replace('\\', os.path.sep))
        if savepath is None:
            savepath = '_' + basename
        try:
            bytes_list = self.builder.mdd_lookup(filepath_in_mdx)
            if bytes_list and not os.path.exists(savepath):
                with open(savepath, 'wb') as f:
                    f.write(bytes_list[0])
                    return savepath
        except sqlite3.OperationalError as e:
            showInfo(str(e))

    def save_media_files(self, data):
        """
        get the necessary static files from local mdx dictionary
        ** kwargs: data = list
        """
        diff = data.difference(self.media_cache['files'])
        self.media_cache['files'].update(diff)
        lst, errors = list(), list()
        wild = [
            '*' + os.path.basename(each.replace('\\', os.path.sep)) for each in diff]
        try:
            for each in wild:
                # TODO : refract get_mdd_keys method
                keys = self.builder.get_mdd_keys(each)
                if not keys:
                    errors.append(each)
                lst.extend(keys)
            for each in lst:
                self.save_file(each)
        except AttributeError:
            pass

        return errors


class StardictService(LocalService):

    def __init__(self, dict_path):
        super(StardictService, self).__init__(dict_path)
        self.query_interval = 0.05
        self.builder = StardictBuilder(self.dict_path, in_memory=False)
        self.builder.get_header()

    @staticmethod
    def support(dict_path):
        return os.path.isfile(dict_path) and dict_path.lower().endswith('.ifo')

    @property
    def title(self):
        if config.use_filename or not self.builder.ifo.bookname:
            return self._filename
        else:
            return self.builder.ifo.bookname.decode('utf-8')

    @export(u"default", 0)
    def fld_whole(self):
        self.builder.check_build()
        try:
            result = self.builder[self.word]
            result = result.strip().replace('\r\n', '<br />') \
                .replace('\r', '<br />').replace('\n', '<br />')
            return QueryResult(result=result)
        except KeyError:
            return QueryResult.default()


class QueryResult(MapDict):
    """Query Result structure"""

    def __init__(self, *args, **kwargs):
        super(QueryResult, self).__init__(*args, **kwargs)
        # avoid return None
        if self['result'] == None:
            self['result'] = ""

    def set_styles(self, **kwargs):
        for key, value in kwargs.items():
            self[key] = value

    @classmethod
    def default(cls):
        return QueryResult(result="")

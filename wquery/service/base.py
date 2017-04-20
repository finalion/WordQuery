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

import inspect
import os
import re
from collections import defaultdict
from functools import wraps

from aqt import mw
from aqt.utils import showInfo, showText
from wquery.context import config
from wquery.libs.mdict.mdict_query import IndexBuilder
from wquery.libs.pystardict import Dictionary
from wquery.utils import MapDict


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


def with_styles(**styles):
    def _with(fld_func):
        @wraps(fld_func)
        def _deco(cls, *args, **kwargs):
            res = fld_func(cls, *args, **kwargs)
            if styles:
                if not isinstance(res, QueryResult):
                    return QueryResult(result=res, **styles)
                else:
                    res.set_styles(**styles)
                    return res
            return res
        return _deco
    return _with


class Service(object):
    '''service base class'''
    Web, Mdx, Stardict = 0, 1, 2

    def __init__(self):
        self._exporters = self.get_exporters()
        self._fields, self._actions = zip(
            *self._exporters) if self._exporters else (None, None)
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
        for each in self.exporters:
            if action_label == each[0]:
                result = each[1]()
                return result if result else QueryResult.default()  # avoid return None
        return QueryResult.default()


class WebService(Service):
    '''web service class'''

    def __init__(self):
        super(WebService, self).__init__()
        self.cache = defaultdict(defaultdict)
        self.query_interval = 1

    def cache_this(self, result):
        self.cache[self.word].update(result)
        return result

    def cached(self, key):
        return (self.word in self.cache) and self.cache[self.word].has_key(key)

    def cache_result(self, key):
        return self.cache[self.word].get(key, '')

    @property
    def title(self):
        return self.__register_label__

    @property
    def unique(self):
        return self.__class__.__name__


class LocalService(Service):

    def __init__(self, dict_path):
        super(LocalService, self).__init__()
        self.dict_path = dict_path
        self.builder = None

    @property
    def unique(self):
        return self.dict_path


class MdxService(LocalService):

    def __init__(self, dict_path):
        super(MdxService, self).__init__(dict_path)
        # self.index()
        # cache all the static files queried, cache builder
        #  {'builder':builder, 'files':[...static files list...]}
        self.cache = defaultdict(set)
        self.query_interval = 0.01

    @staticmethod
    def support(dict_path):
        if dict_path.endswith('.mdx'):
            return True

    @property
    def title(self):
        if self.builder:
            if config.use_filename() or not self.builder._title or self.builder._title.startswith('Title'):
                return os.path.splitext(os.path.basename(self.dict_path))[0]
            else:
                return self.builder._title
        else:
            return os.path.splitext(os.path.basename(self.dict_path))[0]

    def index(self):
        try:
            self.builder = IndexBuilder(self.dict_path)
            if self.builder:
                return True
            return False
        except:
            return False

    @export(u"default", 0)
    def fld_whole(self):
        if not self.builder:
            self.index()
        result = self.builder.mdx_lookup(self.word)
        if result:
            if result[0].upper().find("@@@LINK=") > -1:
                # redirect to a new word behind the equal symol.
                self.word = result[0][len("@@@LINK="):].strip()
                return self.fld_whole()
            else:
                ss = self.adapt_to_anki(result[0])
                # open('d:\\wmu.html', 'wb').write(ss)
                return QueryResult(result=ss[0], js=ss[1])
        return QueryResult.default()

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
        msound = re.findall('href="sound:(.*?\.mp3)"', html)
        if config.export_media():
            media_files_set.update(set(msound))
        for each in media_files_set:
            html = html.replace(each, '_' + each.split('/')[-1])
        # find sounds
        p = re.compile(
            '<a[^>]+?href=\"(sound:_.*?\.(?:mp3|wav))\"[^>]*?>(.*?)</a>')
        html = p.sub("[\\1]\\2", html)
        # showText(html)
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
        diff = data.difference(self.cache['files'])
        self.cache['files'].update(diff)
        lst, errors, styles = list(), list(), list()
        wild = ['*' + os.path.basename(each) for each in diff]
        try:
            for each in wild:
                keys = self.builder.get_mdd_keys(each)
                if not keys:
                    errors.append(each)
                lst.extend(keys)
            for each in lst:
                try:
                    bytes_list = self.builder.mdd_lookup(each)
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


class StardictService(LocalService):

    def __init__(self, dict_path):
        super(StardictService, self).__init__(dict_path)
        self.query_interval = 0.05

    @staticmethod
    def support(dict_path):
        if dict_path.endswith('.ifo'):
            return True

    @property
    def title(self):
        if config.use_filename() or not self.builder.ifo.bookname:
            return os.path.splitext(os.path.basename(self.dict_path))[0]
        else:
            return self.builder.ifo.bookname.decode('utf-8')

    def index(self):
        try:
            self.builder = Dictionary(self.dict_path, in_memory=False)
            if self.builder:
                return True
            return False
        except:
            return False

    @export(u"default", 0)
    def fld_whole(self):
        if not self.builder:
            return
        try:
            result = self.builder[self.word]
            result = result.strip()\
                .replace('\r\n', '<br />')\
                .replace('\r', '<br />')\
                .replace('\n', '<br />')
            return QueryResult(result=result)
        except KeyError:
            return QueryResult.default()


class QueryResult(MapDict):
    """Query Result structure"""

    def __init__(self, *args, **kwargs):
        self['result'] = str()
        super(QueryResult, self).__init__(*args, **kwargs)

    def set_styles(self, **kwargs):
        for key, value in kwargs.items():
            self[key] = value

    @classmethod
    def default(cls):
        return QueryResult(result="")


def register(label):
    """register the dict service with a label, which will be shown in the dicts list."""
    def _deco(cls):
        return _deco
    cls.__register_label__ = label
    return cls


if __name__ == '__main__':
    from youdao import Youdao
    yd = Youdao()
    flds = yd.get_export_flds()
    for each in flds:
        print each.export_fld_label

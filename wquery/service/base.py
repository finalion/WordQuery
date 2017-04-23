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
import shutil
# use ntpath module to ensure the windows-style (e.g. '\\LDOCE.css')
# path can be processed on Unix platform.
# import ntpath
import re
from collections import defaultdict
from functools import wraps

from aqt import mw
from aqt.qt import QFileDialog
from aqt.utils import showInfo, showText
from wquery.context import config
from wquery.libs.mdict.mdict_query import IndexBuilder
from wquery.libs.pystardict import Dictionary
from wquery.utils import MapDict
from wquery.lang import _


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
            cssfile, css, jsfile, js, need_wrap_css, class_wrapper =\
                styles.get('cssfile', None),\
                styles.get('css', None),\
                styles.get('jsfile', None),\
                styles.get('js', None),\
                styles.get('need_wrap_css', False),\
                styles.get('wrap_class', '')

            def wrap(html, css_obj, is_file=True):
                # wrap css and html
                if need_wrap_css and class_wrapper:
                    html = '<div class="{}">{}</div>'.format(
                        class_wrapper, html)
                    return html, wrap_css(css_obj, is_file=is_file, class_wrapper=class_wrapper)[0]
                return html, css_obj

            if cssfile:
                static_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          'static')
                new_cssfile = cssfile if cssfile.startswith(
                    '_') else '_' + cssfile
                # copy the css file to media folder
                copy_static_file(cssfile, new_cssfile)
                # wrap the css file
                res, new_cssfile = wrap(res, new_cssfile)
                res = '<link type="text/css" rel="stylesheet" href="{}" />{}'.format(
                    new_cssfile, res)
            if css:
                res, css = wrap(res, css, is_file=False)
                res = '<styles>{}</styles>{}'.format(css, res)

            if not isinstance(res, QueryResult):
                return QueryResult(result=res, jsfile=jsfile, js=js)
            else:
                res.set_styles(jsfile=jsfile, js=js)
                return res
        return _deco
    return _with


def wrap_css(orig_css, is_file=True, class_wrapper=None, new_cssfile_suffix='wrap'):

    def process(content):
        # clean the comments
        regx = re.compile('/\*.*?\*/', re.DOTALL)
        content = regx.sub('', content).strip()
        # add wrappers to all the selectors except the first one
        regx = re.compile('([^\r\n,{}]+)(,(?=[^}]*{)|\s*{)', re.DOTALL)
        new_css = regx.sub('.%s \\1\\2' % class_wrapper, content)
        return new_css

    if is_file:
        if not class_wrapper:
            class_wrapper = os.path.splitext(os.path.basename(orig_css))[0]
        new_cssfile = '{css_name}_{suffix}.css'.format(
            css_name=orig_css[:orig_css.rindex('.css')],
            suffix=new_cssfile_suffix)
        # if new css file exists, not process
        if os.path.exists(new_cssfile):
            return new_cssfile, class_wrapper
        result = ''
        with open(orig_css, 'rb') as f:
            result = process(f.read().strip())
        if result:
            with open(new_cssfile, 'wb') as f:
                f.write(result)
        return new_cssfile, class_wrapper
    else:
        # class_wrapper must be valid.
        assert class_wrapper
        return process(orig_css), class_wrapper


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
        self.styles = []

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
                return QueryResult(result=ss[0], js=ss[1])
        return QueryResult.default()

    def adapt_to_anki(self, html):
        """
        1. convert the media path to actual path in anki's collection media folder.
        2. remove the js codes (js inside will expires.)
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
        self.save_media_files(media_files_set)
        for cssfile in mcss:
            cssfile = '_' + cssfile
            # if not exists the css file, the user can place the file to media
            # folder first, and it will also execute the wrap process to generate
            # the desired file.
            if os.path.exists(cssfile):
                new_css_file, wrap_class_name = wrap_css(cssfile)
                html = html.replace(cssfile, new_css_file)
                # add global div to the result html
                html = '<div class="{}">{}</div>'.format(wrap_class_name, html)

        js = re.findall('<script.*?>.*?</script>', html, re.DOTALL)
        return unicode(html), '\n'.join(js)

    def save_media_files(self, data):
        """
        get the necessary static files from local mdx dictionary
        ** kwargs: data = list
        """
        diff = data.difference(self.cache['files'])
        self.cache['files'].update(diff)
<<<<<<< HEAD
        lst, errors, styles = list(), list(), list()
        wild = ['*' + os.path.basename(each.replace('\\', os.path.sep))
                for each in diff]
=======
        lst, errors = list(), list()
        wild = ['*' + ntpath.basename(each) for each in diff]
>>>>>>> cd0bb59... wrapping css to avoid styles confusion; supporting static files as service styles; update some webservices
        try:
            for each in wild:
                keys = self.builder.get_mdd_keys(each)
                if not keys:
                    errors.append(each)
                lst.extend(keys)
            for each in lst:
                basename = os.path.basename(each.replace('\\', os.path.sep))
                saved_basename = '_' + basename
                try:
                    bytes_list = self.builder.mdd_lookup(each)
                    if bytes_list:
                        if basename.endswith('.css') or basename.endswith('.js'):
                            self.styles.append(saved_basename)
                        if not os.path.exists(saved_basename):
                            with open(saved_basename, 'wb') as f:
                                f.write(bytes_list[0])
                except sqlite3.OperationalError as e:
                    showInfo(str(e))
        except AttributeError:
            '''
            有些字典会出这样的错误u AttributeError: 'IndexBuilder' object has no attribute '_mdd_db'
            '''
            pass

        return errors


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
            result = result.strip()
                .replace('\r\n', '<br />')
                .replace('\r', '<br />')
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

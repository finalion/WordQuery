#-*- coding:utf-8 -*-
import os
import re
from collections import defaultdict
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo, showText
from wquery.libs.mdict.mdict_query import IndexBuilder
from wquery.libs.pystardict import Dictionary
from wquery.context import config
from .base import (QueryResult, Service, ServiceManager, ServiceProfile,
                   export, with_styles)


class LocalServiceManager(ServiceManager):

    def __init__(self):
        super(LocalServiceManager, self).__init__()

    def index_all(self):
        mw.progress.start(immediate=True, label="Index building...")
        index_thread = self.MdxIndexer(self, self._dict_paths)
        index_thread.start()
        while not index_thread.isFinished():
            mw.app.processEvents()
            index_thread.wait(100)
        mw.progress.finish()

    def get_service_cls(self, path):
        if path.endswith('.mdx'):
            return MdxService
        if path.endswith('.idx') or path.endswith('.idx.gz'):
            return StardictService

    class MdxIndexer(QThread):

        def __init__(self, manager, paths):
            QThread.__init__(self)
            self.manager = manager
            self.paths = paths
            self.index_builders = list()

        def run(self):
            for path in self.paths:
                mw.progress.update(label="Index building...\n%s" %
                                   os.path.basename(path))
                if path.endswith('.mdx'):
                    IndexBuilder(path)
                if path.endswith('.idx') or path.endswith('.idx.gz'):
                    Dictionary(path, in_memory=True)

    def start_all(self):
        self.index_all()
        for service in self.services:
            # showInfo(service.label)
            service.instance = service.cls(service.label)
            service.title = service.instance.title

    def get_available_services(self):
        self._dict_paths = []
        mdx_paths = config.get_dirs()
        for each in mdx_paths:
            for dirpath, dirnames, filenames in os.walk(each):
                self._dict_paths.extend([os.path.join(dirpath, filename)
                                         for filename in filenames if filename.endswith('.mdx') or filename.endswith('.idx') or filename.endswith('.idx.gz')])
                # support mdx dictionary and stardict format dictionary
        self._dict_paths = list(set(self._dict_paths))
        return [ServiceProfile(dict_path, self.get_service_cls(dict_path)) for dict_path in self._dict_paths]

    def update_services(self):
        '''
        mdx services need to be updated at any time, but web services not.
        '''
        self.services = self.get_available_services()
        self.start_all()


class LocalService(Service):
    pass


class MdxService(LocalService):

    def __init__(self, dict_path):
        super(MdxService, self).__init__()
        # showInfo(str(self.exporters))
        self.dict_path = dict_path
        self.builder = None
        self.index()
        # cache all the static files queried, cache builder
        #  {'builder':builder, 'files':[...static files list...]}
        self.cache = defaultdict(set)

    @property
    def title(self):
        if config.use_filename():
            return os.path.basename(self.dict_path)[:-4]
        else:
            self.builder._title = self.builder._title.strip().decode('utf-8')
            return os.path.basename(self.dict_path)[:-4] if not self.builder._title or self.builder._title.startswith('Title') else self.builder._title

    def index(self):
        self.builder = IndexBuilder(self.dict_path)

    @export(u"完整解释", 0)
    def fld_whole(self):
        if not self.builder:
            self.index()
        result = self.builder.mdx_lookup(self.word)
        if result:
            if result.upper().startswith("@@@LINK="):
                # redirect to a new word behind the equal symol.
                self.word = result[8:]
                return self.fld_whole()
            else:
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
            # showInfo(str(errors))
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
        super(StardictService, self).__init__()
        # showInfo(str(self.exporters))
        self.dict_path = dict_path
        self.builder = None
        self.index()

    @property
    def title(self):
        if config.use_filename():
            return os.path.basename(self.dict_path)[:-4]
        else:
            return self.builder.ifo.bookname.decode('utf-8')

    def index(self):
        self.builder = Dictionary(self.dict_path, in_memory=True)

    @export(u"default", 0)
    def fld_whole(self):
        if not self.builder:
            self.index()
        try:
            result = self.builder[self.word]
            return QueryResult(result=result) if result else self.default_result
        except:
            return self.default_result

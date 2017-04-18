#-*- coding:utf-8 -*-
import inspect
import os
from functools import wraps

from aqt import mw
from aqt.qt import QThread
from aqt.utils import showInfo
from wquery.context import config
from wquery.libs.mdict.mdict_query import IndexBuilder
from wquery.utils import MapDict, importlib

from .base import MdxService, StardictService, WebService


class ServiceManager(object):

    def __init__(self):
        self.web_services = self.get_available_web_services()
        self.local_services = self.get_available_local_services()

    @property
    def services(self):
        return self.web_services + self.local_services

    def register(self, service):
        pass

    def start_all(self):
        self.index_all_mdxs()
        # make all local services available
        for service in self.local_services:
            if not service.index():
                # showInfo(service.dict_path)
                self.local_services.remove(service)

    def update_services(self):
        self.web_services = self.get_available_web_services()
        self.local_services = self.get_available_local_services()
        self.start_all()

    def get_service(self, unique):
        # webservice unique: class name
        # mdxservice unique: dict filepath
        for each in self.services:
            if each.unique == unique:
                return each

    def get_service_action(self, service, label):
        for each in service.fields:
            if each.label == label:
                return each

    def get_available_web_services(self):
        services = []
        mypath = os.path.dirname(os.path.realpath(__file__))
        files = [f for f in os.listdir(mypath)
                 if f not in ('__init__.py', 'base.py', 'localservice.py', 'webservice.py')
                 and not f.endswith('.pyc')]

        for f in files:
            # try:
            module = importlib.import_module(
                '.%s' % os.path.splitext(f)[0], __package__)
            for name, cls in inspect.getmembers(module, predicate=inspect.isclass):
                if issubclass(cls, WebService) and cls is not WebService:
                    label = getattr(cls, '__register_label__', cls.__name__)
                    service = cls()
                    if service not in services:
                        services.append(service)
        return services

    def get_available_local_services(self):
        self.local_dict_paths = []
        mdx_paths = config.get_dirs()
        services = []
        for each in mdx_paths:
            for dirpath, dirnames, filenames in os.walk(each):
                for filename in filenames:
                    dict_path = os.path.join(dirpath, filename)
                    if MdxService.support(dict_path):
                        services.append(MdxService(dict_path))
                    if StardictService.support(dict_path):
                        services.append(StardictService(dict_path))
                # support mdx dictionary and stardict format dictionary
        self._dict_paths = [service.dict_path for service in services]
        return services

    def index_all_mdxs(self):
        mw.progress.start(immediate=True, label="Index building...")
        index_thread = self.MdxIndexer(self, self._dict_paths)
        index_thread.start()
        while not index_thread.isFinished():
            mw.app.processEvents()
            index_thread.wait(100)
        mw.progress.finish()

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
                if MdxService.support(path):
                    IndexBuilder(path)

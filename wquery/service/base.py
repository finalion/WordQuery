#-*- coding:utf-8 -*-
import inspect
from functools import wraps
import os
from wquery.utils import importlib
from aqt.utils import showInfo


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton


class ServiceProfile(object):

    def __init__(self, label, cls, instance=None):
        self.label = label
        self.cls = cls
        self.instance = instance


@singleton
class ServiceManager(object):

    def __init__(self):
        self.services = self.get_package_services()

    def register(self, service):
        pass

    def start(service):
        service.cls()

    def start_all(self):
        for service in self.services:
            service.instance = service.cls()

    def get_service(self, label):
        for each in self.services:
            if each.label == label:
                return each

    def get_service_action(self, service, label):
        for each in service.fields:
            if each.label == label:
                return each

    def get_package_services(self):
        services = []
        mypath = os.path.dirname(os.path.realpath(__file__))
        files = [f for f in os.listdir(mypath) if f not in (
            '__init__.py', 'base.py', 'importlib.py') and not f.endswith('.pyc')]

        for f in files:
            # try:
            module = importlib.import_module('.%s' % f[:-3], __package__)
            for name, cls in inspect.getmembers(module, predicate=inspect.isclass):
                if cls is not Service and issubclass(cls, Service):
                    label = getattr(cls, '__register_label__', name)
                    sp = ServiceProfile(label, cls)
                    if sp not in services:
                        services.append(sp)
        return services
        # except ImportError:
        #     showInfo('Import Error')
        #     pass
        # showInfo(str(self.services))


class Service(object):

    def __init__(self):
        self._exporters = self.get_exporters()
        self._fields, self._actions = zip(
            *self._exporters) if self._exporters else (None, None)

    @property
    def fields(self):
        return self._fields

    @property
    def actions(self):
        return self._actions

    @property
    def exporters(self):
        return self._exporters

    def active(self, action_label, word):
        self.word = word
        # showInfo('service active: %s ##%s##' % (action_label, word))
        for each in self.exporters:
            if action_label == each[0]:
                result = each[1]()
                return result if result else ""  # avoid return None
        return ""

    def get_exporters(self):
        flds = dict()
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for method in methods:
            export_attrs = getattr(method[1], '__export_attrs__', None)
            if export_attrs:
                label, index = export_attrs
                flds.update({int(index): (label, method[1])})
        sorted_flds = sorted(flds)
        # label, function
        return [flds[key] for key in sorted_flds]

# define decorators below----------------------------


def register(label):
    """register the dict service with a label, which will be shown in the dicts list."""
    def _deco(cls):
        return _deco
    cls.__register_label__ = label
    return cls


def export(label, index):
    """export dict field function with a label, which will be shown in the fields list."""
    def _with(fld_func):
        @wraps(fld_func)
        def _deco(cls, *args, **kwargs):
            return fld_func(cls, *args, **kwargs)
        _deco.__export_attrs__ = (label, index)
        return _deco
    return _with


def with_css(css):
    def _with(fld_func):
        def _deco(cls, *args, **kwargs):
            return css + fld_func(cls, *args, **kwargs)
        return _deco
    return _with

if __name__ == '__main__':
    from youdao import Youdao
    yd = Youdao()
    flds = yd.get_export_flds()
    for each in flds:
        print each.export_fld_label

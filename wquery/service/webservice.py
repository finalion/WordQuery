#-*- coding:utf-8 -*-
import os
import inspect

from wquery.utils import importlib

from .base import Service, QueryResult, ServiceProfile, ServiceManager


class WebServiceManager(ServiceManager):

    def __init__(self):
        super(WebServiceManager, self).__init__()

    def get_available_services(self):
        services = []
        mypath = os.path.dirname(os.path.realpath(__file__))
        files = [f for f in os.listdir(mypath) if f not in (
            '__init__.py', 'base.py', 'importlib.py') and not f.endswith('.pyc')]

        for f in files:
            # try:
            module = importlib.import_module('.%s' % f[:-3], __package__)
            for name, cls in inspect.getmembers(module, predicate=inspect.isclass):
                if issubclass(cls, WebService):
                    label = getattr(cls, '__register_label__', None)
                    if label:
                        sp = ServiceProfile(label, cls)
                        if sp not in services:
                            services.append(sp)
        return services
        # except ImportError:
        #     showInfo('Import Error')
        #     pass
        # showInfo(str(self.services))


class WebService(Service):
    '''web service class'''

    def __init__(self):
        super(WebService, self).__init__()

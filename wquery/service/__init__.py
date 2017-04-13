#-*- coding:utf-8 -*-
from .youdao import Youdao
from .webservice import WebServiceManager
from .localservice import LocalServiceManager

web_service_manager = WebServiceManager()
local_service_manager = LocalServiceManager()


def start_services():
    web_service_manager.start_all()
    local_service_manager.start_all()

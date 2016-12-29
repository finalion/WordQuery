#-*- coding:utf-8 -*-
from .youdao import Youdao
from .webservice import WebServiceManager
from .mdxservice import MdxServiceManager

web_service_manager = WebServiceManager()
mdx_service_manager = MdxServiceManager()


def start_services():
    web_service_manager.start_all()
    mdx_service_manager.start_all()

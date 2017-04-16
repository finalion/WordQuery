#-*- coding:utf-8 -*-
from .manager import ServiceManager

service_manager = ServiceManager()


def start_services():
    service_manager.start_all()

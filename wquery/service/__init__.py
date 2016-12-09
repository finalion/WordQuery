#-*- coding:utf-8 -*-
from .base import Service, ServiceManager

service_manager = ServiceManager()
service_manager.start_all()

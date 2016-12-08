#-*- coding:utf-8 -*-
from .youdao import Youdao
from .base import Service


def register(service):
    pass

services = [
    {'label': u'有道词典', 'cls': Youdao},
]

Service.start(services)


def find_service(label):
    for each in services:
        if each['label'] == label:
            return each


def find_service_action(service, label):
    for each in service.fields:
        if each['label'] == label:
            return each

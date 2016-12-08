#-*- coding:utf-8 -*-


class Service(object):

    def __init__(self):
        pass

    @classmethod
    def start(cls, services):
        for service in services:
            service['instance'] = service['cls']()

    def active(self, action_label, word):
        for each in self.fields:
            if action_label == each['label']:
                return each['action'](word)

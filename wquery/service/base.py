#-*- coding:utf-8 -*-
import inspect


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

    def get_export_flds(self):
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        return [m[1] for m in methods if m[0].startswith('export_fld_')]


if __name__ == '__main__':
    def label(label):
        def _with(fld_func):

            def _deco(cls):
                fld_func.export_fld_label = label
            return _deco
        return _with

    class test(Service):

        @label('fllabel')
        def export_fld_f1(self):
            return 'f1'

        @label('f2label')
        def export_fld_f2(self):
            return 'f2'

        @label('f3label')
        def export_fld_f3(self):
            return 'f3'
    yd = test()
    flds = yd.get_export_flds()
    for each in flds:
        print each.export_fld_label

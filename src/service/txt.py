#-*- coding:utf-8 -*-
import re

from aqt.utils import showInfo, showText
from .base import LocalService, export, register, with_styles

path = u'D:\\dicts\\LDOCE\\d.txt'


@register(u'txt测试')
class TxtTest(LocalService):

    def __init__(self):
        super(TxtTest, self).__init__(path)
        try:
            self.handle = open(path, 'rb')
        except:
            self.handle = None

    @export(u'all', 1)
    def fld_phonetic(self):
        if not self.handle:
            return
        for line in self.handle:
            line = line.decode("UTF-8")
            m = re.search(self.word, line)
            if m:
                return line

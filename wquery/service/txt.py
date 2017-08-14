#-*- coding:utf-8 -*-
import re

from aqt.utils import showInfo, showText
from base import TxtService, export, register, with_styles

path = u'/Users/yu/Downloads/q/aaa.txt'


@register(u'txt测试')
class TxtTest(TxtService):

    def __init__(self):
        super(TxtTest, self).__init__(path)

    # @property
    # def unique(self):
    #     return self.__class__.__name__

    @export(u'自制例句', 1)
    def fld_sentence(self):
        with open(self.dict_path, 'rb') as f:
            lines = f.readlines()
            for line in lines: 
                line = line.decode("UTF-8")
                m=re.search(self.word,line)       
                if m:
                    return line
        return ''


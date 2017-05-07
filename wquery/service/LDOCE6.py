#-*- coding:utf-8 -*-
import re

from aqt.utils import showInfo, showText

from .base import export, with_styles, register, MdxService

path = u'C:\\Users\\surface\\Documents\\dicts\\LDOCE\\LDOCE6.mdx'


@register(u'本地词典解析Sample-LDOCE6')
class Ldoce6(MdxService):

    def __init__(self, dict_path):
        super(Ldoce6, self).__init__(path)

    @property
    def unique(self):
        return self.__class__.__name__

    @property
    def title(self):
        return self.__register_label__

    @export(u'音标', 1)
    def fld_phonetic(self):
        html = self.get_html()
        m = re.search(r'<span class="pron">(.*?)</span>', html)
        if m:
            return m.groups()[0]
        return ''

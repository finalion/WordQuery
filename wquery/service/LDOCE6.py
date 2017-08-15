#-*- coding:utf-8 -*-
import re
import random


from aqt.utils import showInfo, showText

from .base import export, with_styles, register, MdxService

path = u'/Users/yu/Documents/english study/mdx/LDOCE6双解/L6mp3.mdx'


@register(u'本地词典-LDOCE6')
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

    @export(u'Bre单词发音', 2)
    def fld_voicebre(self):
        html = self.get_html()
        m = re.search(r'<span class="brevoice">(.*?)</span brevoice>', html)
        if m:
            return m.groups()[0]
        return ''
		
    @export(u'Ame单词发音', 3)
    def fld_voiceame(self):
        html = self.get_html()
        m = re.search(r'<span class="amevoice">(.*?)</span amevoice>', html)
        if m:
            return m.groups()[0]
        return ''

    @export(u'sentence', 4)
    def fld_sentence(self):
        html = self.get_html()
        m = re.search(r'<span class="example">(.*?)</span example>', html)
        if m:
            return re.sub('<img.*?png">','',m.groups()[0])
        return ''
		
    @export(u'def', 5)
    def fld_definate(self):
        html = self.get_html()
        m = re.search(r'<span class="def">(.*?)</span def>', html)
        if m:
            return m.groups()[0]
        return ''
		
    @export(u'random_sentence', 6)
    def fld_random_sentence(self):
        html = self.get_html()
        m = re.findall(r'<span class="example">(.*?)</span example>', html)
        if m:
            number=len(m)
            index = random.randrange(0,number-1,1)
            return re.sub('<img.*?png">','',m[index])
        return ''

    @export(u'all sentence', 7)
    def fld_allsentence(self):
	html = self.get_html()
	m=re.findall(r'(<span class="example">.+?</span example><span class="example_c">.+?</span example_c>)',html)
	if m:
		items=0
		my_str=''
		for items in range(len(m)):
			my_str=my_str+m[items]
		return my_str
	return ''
	

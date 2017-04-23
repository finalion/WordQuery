#-*- coding:utf-8 -*-
import re
import urllib
import urllib2
import xml.etree.ElementTree
from collections import defaultdict

from aqt.utils import showInfo

from .base import WebService, export, with_styles, register


@register(u'有道词典-法语')
class Youdaofr(WebService):

    def __init__(self):
        super(Youdaofr, self).__init__()

    def _get_from_api(self, lang='fr'):
        url = "http://dict.youdao.com/fsearch?client=deskdict&keyfrom=chrome.extension&pos=-1&doctype=xml&xmlVersion=3.2&dogVersion=1.0&vendor=unknown&appVer=3.1.17.4208&le=%s&q=%s" % (
            lang, self.word)
        explains = ''
        try:
            result = urllib2.urlopen(url, timeout=5).read()
            # showInfo(str(result))
            doc = xml.etree.ElementTree.fromstring(result)
            # fetch explanations
            explains = '<br>'.join([node.text for node in doc.findall(
                ".//custom-translation/translation/content")])
            return self.cache_this({'explains': explains})
        except:
            return {'explains': explains}

    @export(u'基本释义', 1)
    def fld_explains(self):
        return self.cache_result('explains') if self.cached('explains') else \
            self._get_from_api().get('explains', '')

    @with_styles(cssfile='_youdao.css', need_wrap_css=True, wrap_class='youdao')
    def _get_singledict(self, single_dict, lang='fr'):
        url = "http://m.youdao.com/singledict?q=%s&dict=%s&le=%s&more=false" % (
            self.word, single_dict, lang)
        try:
            result = urllib2.urlopen(url, timeout=5).read()
            return '<div id="%s_contentWrp" class="content-wrp dict-container"><div id="%s" class="trans-container %s ">%s</div></div><div id="outer"><audio id="dictVoice" style="display: none"></audio></div>' % (single_dict, single_dict, single_dict, result)
        except:
            return ''

    # @export(u'英英释义', 4)
    # def fld_ee(self):
    #     return self._get_singledict('ee')

    @export(u'网络释义', 5)
    def fld_web_trans(self):
        return self._get_singledict('web_trans')

    @export(u'双语例句', 8)
    def fld_blng_sents_part(self):
        return self._get_singledict('blng_sents_part')

    @export(u'百科', 11)
    def fld_baike(self):
        return self._get_singledict('baike')

    @export(u'汉语词典(中)', 13)
    def fld_hh(self):
        return self._get_singledict('hh')

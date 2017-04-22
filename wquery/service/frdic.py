#-*- coding:utf-8 -*-
import base64
import re
import urllib
import urllib2
from collections import defaultdict

from aqt.utils import showInfo
from BeautifulSoup import BeautifulSoup

from .base import WebService, export, with_styles, register

# Anki buit-in BeautifulSoup is bs3 not bs4


css = ''


@register(u'法语助手')
class Frdic(WebService):

    def __init__(self):
        super(Frdic, self).__init__()

    def _get_content(self):
        url = 'https://frdic.com/mdicts/fr/{word}'.format(
            word=urllib.quote(self.word.encode()))
        try:
            result = {}
            html = urllib2.urlopen(url, timeout=5).read()
            soup = BeautifulSoup(html)

            def _get_from_element(dict, key, soup, tag, id=None, class_=None):
                baseURL = 'https://frdic.com/'
                # element = soup.find(tag, id=id, class_=class_)  # bs4
                if id:
                    element = soup.find(tag, {"id": id})
                if class_:
                    element = soup.find(tag, {"class": class_})
                if element:
                    dict[key] = str(element)
                    dict[key] = re.sub(
                        r'href="/', 'href="' + baseURL, dict[key])
                    dict[key] = re.sub(r'声明：.*。', '', dict[key])
                    dict[key] = dict[key].decode('utf-8')
                return dict

            # '<span class="Phonitic">[bɔ̃ʒur]</span>'
            result = _get_from_element(
                result, 'phonitic', soup, 'span', class_='Phonitic')
            # '<div id='FCChild'  class='expDiv'>'
            result = _get_from_element(
                result, 'fccf', soup, 'div', id='FCChild')  # 法汉-汉法词典
            result = _get_from_element(
                result, 'example', soup, 'div', id='LJChild')  # 法语例句库
            result = _get_from_element(
                result, 'syn', soup, 'div', id='SYNChild')  # 近义、反义、派生词典
            result = _get_from_element(
                result, 'ff', soup, 'div', id='FFChild')  # 法法词典
            result = _get_from_element(
                result, 'fe', soup, 'div', id='FEChild')  # 法英词典

            return self.cache_this(result)
        except Exception as e:
            return {}

    #@export(u'真人发音', 0)
    def fld_sound(self):
        # base64.b64encode('bonjour') == 'Ym9uam91cg=='
        # https://api.frdic.com/api/v2/speech/speakweb?langid=fr&txt=QYNYm9uam91cg%3d%3d
        url = 'https://api.frdic.com/api/v2/speech/speakweb?langid=fr&txt=QYN{word}'.format(
            word=urllib.quote(base64.b64encode(self.word.encode())))
        audio_name = 'frdic_{word}.mp3'.format(word=self.word.encode())
        try:
            urllib.urlretrieve(url, 'frdic_{word}.mp3'.format(word=self.word))
            return '[sound: %s]' % audio_name
        except Exception as e:
            return ''

    @export(u'音标', 1)
    def fld_phonetic(self):
        return self.cache_result('phonitic') if self.cached('phonitic') else self._get_content().get('phonitic', '')

    @export(u'法汉-汉法词典', 2)
    @with_styles(css=css)
    def fld_fccf(self):
        return self.cache_result('fccf') if self.cached('fccf') else self._get_content().get('fccf', '')

    @export(u'法语例句库', 3)
    @with_styles(css=css)
    def fld_example(self):
        return self.cache_result('example') if self.cached('example') else self._get_content().get('example', '')

    @export(u'近义、反义、派生词典', 4)
    @with_styles(css=css)
    def fld_syn(self):
        return self.cache_result('syn') if self.cached('syn') else self._get_content().get('syn', '')

    @export(u'法法词典', 5)
    @with_styles(css=css)
    def fld_ff(self):
        return self.cache_result('ff') if self.cached('ff') else self._get_content().get('ff', '')

    @export(u'法英词典', 6)
    @with_styles(css=css)
    def fld_fe(self):
        return self.cache_result('fe') if self.cached('fe') else self._get_content().get('fe', '')

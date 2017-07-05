#-*- coding:utf-8 -*-
import json
import os
import re
import urllib
import urllib2
import xml.etree.ElementTree
from collections import defaultdict

from aqt.utils import showInfo

from .base import WebService, export, register
from wquery.odds import ignore_exception

bcz_download_mp3 = True
bcz_download_img = True


@register(u'百词斩')
class Baicizhan(WebService):

    def __init__(self):
        super(Baicizhan, self).__init__()

    def _get_from_api(self):
        url = u"http://mall.baicizhan.com/ws/search?w={word}".format(
            word=self.word)
        try:
            html = urllib2.urlopen(url, timeout=5).read()
            return self.cache_this(json.loads(html))
        except:
            return defaultdict(str)

    # @ignore_exception
    @export(u'发音', 0)
    def fld_phonetic(self):
        url = u'http://baicizhan.qiniucdn.com/word_audios/{word}.mp3'.format(
            word=self.word)
        audio_name = 'bcz_%s.mp3' % self.word
        if bcz_download_mp3:
            urllib.urlretrieve(url, audio_name)
            with open(audio_name, 'rb') as f:
                if f.read().strip() == '{"error":"Document not found"}':
                    os.remove(audio_name)
                    return ''
            return self.get_anki_label(audio_name, 'audio')
        else:
            return url

    def _get_field(self, key, default=u''):
        return self.cache_result(key) if self.cached(key) else self._get_from_api().get(key, default)

    @export(u'音标', 1)
    def fld_explains(self):
        return self._get_field('accent')

    @export(u'图片', 2)
    def fld_img(self):
        url = self._get_field('img')
        if url and bcz_download_img:
            filename = url[url.rindex('/') + 1:]
            if self.download(url, filename):
                return self.get_anki_label(filename, 'img')
        return self.get_anki_label(url, 'img')

    @export(u'象形', 3)
    def fld_df(self):
        url = self._get_field('df')
        if url and bcz_download_img:
            filename = url[url.rindex('/') + 1:]
            if self.download(url, filename):
                return self.get_anki_label(filename, 'img')
        return self.get_anki_label(url, 'img')

    @export(u'中文释义', 6)
    def fld_mean(self):
        return self._get_field('mean_cn')

    @export(u'英文例句', 4)
    def fld_st(self):
        return self._get_field('st')

    @export(u'例句翻译', 5)
    def fld_sttr(self):
        return self._get_field('sttr')

    @export(u'单词tv', 7)
    def fld_tv_url(self):
        return self.get_anki_label(self._get_field('tv'), 'video')

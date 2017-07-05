#-*- coding:utf-8 -*-
import os
import re
import urllib2
import json
from collections import defaultdict
from aqt.utils import showInfo, showText

from .base import WebService, export, with_styles, register
from wquery.odds import ignore_exception

iciba_download_mp3 = True


@register(u'爱词霸')
class ICIBA(WebService):

    def __init__(self):
        super(ICIBA, self).__init__()

    def _get_content(self):
        resp = defaultdict(str)
        headers = {
            'Accept-Language': 'en-US,zh-CN;q=0.8,zh;q=0.6,en;q=0.4',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01'}
        # try:
        request = urllib2.Request(
            'http://www.iciba.com/index.php?a=getWordMean&c=search&word=' + self.word.encode('utf-8'), headers=headers)
        resp = json.loads(urllib2.urlopen(request).read())
        # self.cache_this(resp['baesInfo']['symbols'][0])
        # self.cache_this(resp['sentence'])
        # showText(str(self.cache[self.word]))
        # return self.cache[self.word]
        return self.cache_this(resp)
        # except Exception as e:
        #     return resp

    def _get_field(self, key, default=u''):
        return self.cache_result(key) if self.cached(key) else self._get_content().get(key, default)

    @ignore_exception
    @export(u'美式音标', 1)
    def fld_phonetic_us(self):
        seg = self._get_field('baesInfo')
        return seg['symbols'][0]['ph_am']

    @ignore_exception
    @export(u'英式音标', 2)
    def fld_phonetic_uk(self):
        seg = self._get_field('baesInfo')
        return seg['symbols'][0]['ph_en']

    @ignore_exception
    @export(u'美式发音', 3)
    def fld_mp3_us(self):
        seg = self._get_field('baesInfo')
        audio_url, t = seg['symbols'][0]['ph_am_mp3'], 'am'
        if not audio_url:
            audio_url, t = seg['symbols'][0]['ph_tts_mp3'], 'tts'
        if iciba_download_mp3 and audio_url:
            filename = u'iciba_{0}_{1}.mp3'.format(self.word, t)
            if os.path.exists(filename) or self.download(audio_url, filename):
                return self.get_anki_label(filename, 'audio')
        return audio_url

    @ignore_exception
    @export(u'英式发音', 4)
    def fld_mp3_uk(self):
        seg = self._get_field('baesInfo')
        audio_url, t = seg['symbols'][0]['ph_en_mp3'], 'en'
        if not audio_url:
            audio_url, t = seg['symbols'][0]['ph_tts_mp3'], 'tts'
        if iciba_download_mp3 and audio_url:
            filename = u'iciba_{0}_{1}.mp3'.format(self.word, t)
            if os.path.exists(filename) or self.download(audio_url, filename):
                return self.get_anki_label(filename, 'audio')
        return audio_url

    @ignore_exception
    @export(u'释义', 5)
    def fld_definition(self):
        seg = self._get_field('baesInfo')
        parts = seg['symbols'][0]['parts']
        return u'<br>'.join([part['part'] + ' ' + '; '.join(part['means']) for part in parts])

    @ignore_exception
    @export(u'双语例句', 6)
    def fld_samples(self):
        sentences = ''
        segs = self._get_field('sentence')
        for i, seg in enumerate(segs):
            sentences = sentences +\
                u"""<li>
                        <div class="sen_en">{0}</div>
                        <div class="sen_cn">{1}</div>
                    </li>""".format(seg['Network_en'], seg['Network_cn'])
        return u"""<ol>{}</ol>""".format(sentences)

    @ignore_exception
    @export(u'权威例句', 7)
    def fld_auth_sentence(self):
        sentences = ''
        segs = self._get_field('auth_sentence')
        for i, seg in enumerate(segs):
            sentences = sentences +\
                u"""<li>{0}  [{1}]</li>""".format(
                    seg['res_content'], seg['source'])
        return u"""<ol>{}</ol>""".format(sentences)

    @ignore_exception
    @export(u'句式用法', 8)
    def fld_usage(self):
        sentences = ''
        segs = self._get_field('jushi')
        for i, seg in enumerate(segs):
            sentences = sentences +\
                u"""<li>
                        <div class="sen_en">{0}</div>
                        <div class="sen_cn">{1}</div>
                    </li>""".format(seg['english'], seg['chinese'])
        return u"""<ol>{}</ol>""".format(sentences)

    @ignore_exception
    @export(u'使用频率', 9)
    def fld_frequence(self):
        seg = self._get_field('baesInfo')
        return str(seg['frequence'])

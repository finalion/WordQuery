#-*- coding:utf-8 -*-
import re
import urllib2
import json

from aqt.utils import showInfo, showText

from .base import WebService, export, with_styles, register

bing_download_mp3 = True


@register(u'Bing xtk')
class BingXtk(WebService):

    def __init__(self):
        super(BingXtk, self).__init__()

    def _get_content(self):
        resp = {'pronunciation': '', 'defs': '', 'sams': ''}
        headers = {
            'Accept-Language': 'en-US,zh-CN;q=0.8,zh;q=0.6,en;q=0.4',
            'User-Agent': 'WordQuery Addon (Anki)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
        try:
            request = urllib2.Request(
                'http://xtk.azurewebsites.net/BingDictService.aspx?Word=' + self.word.encode('utf-8'), headers=headers)
            resp = json.loads(urllib2.urlopen(request).read())
            return self.cache_this(resp)
        except Exception as e:
            return resp

    def _get_field(self, key, default=u''):
        return self.cache_result(key) if self.cached(key) else self._get_content().get(key, default)

    def _get_subfield(self, field, key, default=u''):
        subfield = default
        if field:
            subfield = field.get(key, default)
            if subfield is None:
                subfield = default
        return subfield

    @export(u'美式音标', 1)
    def fld_phonetic_us(self):
        seg = self._get_field('pronunciation')
        return self._get_subfield(seg, 'AmE')

    @export(u'英式音标', 2)
    def fld_phonetic_uk(self):
        seg = self._get_field('pronunciation')
        return self._get_subfield(seg, 'BrE')

    @export(u'美式发音', 3)
    def fld_mp3_us(self):
        seg = audio_url = self._get_field('pronunciation')
        audio_url = self._get_subfield(seg, 'AmEmp3')
        if bing_download_mp3 and audio_url:
            filename = u'_bing_{}_us.mp3'.format(self.word)
            if self.download(audio_url, filename):
                return self.get_anki_label(filename, 'audio')
        return audio_url

    @export(u'英式发音', 4)
    def fld_mp3_uk(self):
        seg = self._get_field('pronunciation')
        audio_url = self._get_subfield(seg, 'BrEmp3')
        if bing_download_mp3 and audio_url:
            filename = u'_bing_{}_br.mp3'.format(self.word)
            if self.download(audio_url, filename):
                return self.get_anki_label(filename, 'audio')
        return audio_url

    @export(u'释义', 5)
    def fld_definition(self):
        segs = self._get_field('defs')
        return u'<br>'.join([u'<span class="pos"><b>{0}</b> </span><span class="def"><span>{1}</span></span>'.format(seg['pos'], seg['def']) for seg in segs])

    @export(u'例句', 6)
    # @with_styles(cssfile='_bing2.css', need_wrap_css=True, wrap_class=u'bing')
    def fld_samples(self):
        max_numbers = 10
        segs = self._get_field('sams')
        sentences = ''
        for i, seg in enumerate(segs):
            sentences = sentences +\
                u"""<li><div class="se_li1">
                        <div class="se_li1">
                            <div class="sen_en">{0}</div>
                            <div class="sen_cn">{1}</div>
                        </div>
                    </div></li>""".format(seg['eng'], seg['chn'], i + 1)
            if i == 9:
                break
        return u"""<div class="se_div">
                        <div class="sentenceCon">
                            <div id="sentenceSeg"><ol>{}</ol></div>
                        </div>
                </div>""".format(sentences)

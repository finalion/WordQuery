#-*- coding:utf-8 -*-
import re
import urllib2
import xml.etree.ElementTree

from aqt.utils import showInfo

from .base import WebService, export, with_styles, register

js = '''
var initVoice = function () {
    var player = document.getElementById('dictVoice');
    document.addEventListener('click', function (e) {
        var target = e.target;
        if (target.hasAttribute('role') && target.getAttribute('role').indexOf('dict_audio_js') >= 0) {
            var url = target.getAttribute('data-rel');
            player.setAttribute('src', url);
            player.volume = 1;
            player.play();
            e.preventDefault();
        }
    }, false);
};
initVoice();
'''

youdao_download_mp3 = True


@register(u'有道词典')
class Youdao(WebService):

    def __init__(self):
        super(Youdao, self).__init__()

    def _get_from_api(self, lang='eng'):
        url = "http://dict.youdao.com/fsearch?client=deskdict&keyfrom=chrome.extension&pos=-1&doctype=xml&xmlVersion=3.2&dogVersion=1.0&vendor=unknown&appVer=3.1.17.4208&le=%s&q=%s" % (
            lang, self.word)
        phonetics, explains = '', ''
        try:
            result = urllib2.urlopen(url, timeout=5).read()
            # showInfo(str(result))
            doc = xml.etree.ElementTree.fromstring(result)
            # fetch symbols
            symbol, uk_symbol, us_symbol = doc.findtext(".//phonetic-symbol"), doc.findtext(
                ".//uk-phonetic-symbol"), doc.findtext(".//us-phonetic-symbol")
            if uk_symbol and us_symbol:
                phonetics = 'UK [%s]   US [%s]' % (uk_symbol, us_symbol)
            elif symbol:
                phonetics = '[%s]' % symbol
            else:
                phonetics = ''
            # fetch explanations
            explains = '<br>'.join([node.text for node in doc.findall(
                ".//custom-translation/translation/content")])
            return self.cache_this({'phonetic': phonetics, 'explains': explains})
        except:
            return {'phonetic': phonetics, 'explains': explains}

    @export(u'音标', 0)
    def fld_phonetic(self):
        return self.cache_result('phonetic') if self.cached('phonetic') else self._get_from_api()['phonetic']

    @export(u'基本释义', 1)
    def fld_explains(self):
        return self.cache_result('explains') if self.cached('explains') else self._get_from_api()['explains']

    @with_styles(cssfile='_youdao.css', js=js, need_wrap_css=True, wrap_class='youdao')
    def _get_singledict(self, single_dict, lang='eng'):
        url = u"http://m.youdao.com/singledict?q={0}&dict={1}&le={2}&more=false".format(
            self.word, single_dict, lang)
        try:
            result = urllib2.urlopen(url, timeout=5).read()
            return u'<div id="{0}_contentWrp" class="content-wrp dict-container"><div id="{0}" class="trans-container {0} ">{1}</div></div><div id="outer"><audio id="dictVoice" style="display: none"></audio></div>'.format(single_dict, result.decode('utf-8'))
        except:
            return ''

    @export(u'英式发音', 2)
    def fld_british_audio(self):
        audio_url = u'http://dict.youdao.com/dictvoice?audio={}&type=1'.format(
            self.word)
        if youdao_download_mp3:
            filename = u'_youdao_{}_uk.mp3'.format(self.word)
            if self.download(audio_url, filename):
                return self.get_anki_label(filename, 'audio')
        return audio_url

    @export(u'美式发音', 3)
    def fld_american_audio(self):
        audio_url = u'http://dict.youdao.com/dictvoice?audio={}&type=2'.format(
            self.word)
        if youdao_download_mp3:
            filename = u'_youdao_{}_us.mp3'.format(self.word)
            if self.download(audio_url, filename):
                return self.get_anki_label(filename, 'audio')
        return audio_url

    @export(u'柯林斯英汉', 4)
    def fld_collins(self):
        return self._get_singledict('collins')

    @export(u'21世纪', 5)
    def fld_ec21(self):
        return self._get_singledict('ec21')

    @export(u'英英释义', 6)
    def fld_ee(self):
        return self._get_singledict('ee')

    @export(u'网络释义', 7)
    def fld_web_trans(self):
        return self._get_singledict('web_trans')

    @export(u'同根词', 8)
    def fld_rel_word(self):
        return self._get_singledict('rel_word')

    @export(u'同近义词', 9)
    def fld_syno(self):
        return self._get_singledict('syno')

    @export(u'双语例句', 10)
    def fld_blng_sents_part(self):
        return self._get_singledict('blng_sents_part')

    @export(u'原生例句', 11)
    def fld_media_sents_part(self):
        return self._get_singledict('media_sents_part')

    @export(u'权威例句', 12)
    def fld_auth_sents_part(self):
        return self._get_singledict('auth_sents_part')

    @export(u'新英汉大辞典(中)', 13)
    def fld_ce_new(self):
        return self._get_singledict('ce_new')

    @export(u'百科', 14)
    def fld_baike(self):
        return self._get_singledict('baike')

    @export(u'汉语词典(中)', 15)
    def fld_hh(self):
        return self._get_singledict('hh')

    @export(u'专业释义(中)', 16)
    def fld_special(self):
        return self._get_singledict('special')

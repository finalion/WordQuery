# -*- coding:utf-8 -*-
import re

try:
    import urllib2
except:
    import urllib.request as urllib2
import xml.etree.ElementTree

from .base import WebService, export, register, with_styles

from bs4 import BeautifulSoup, Tag, NavigableString

from warnings import filterwarnings

filterwarnings("ignore")

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
            self.word, 'collins' if single_dict == 'collins_eng' else single_dict, lang)
        try:
            result = urllib2.urlopen(url, timeout=5).read()
            html = """
            <div id="{0}_contentWrp" class="content-wrp dict-container">
                <div id="{0}" class="trans-container {0} ">{1}</div>
            </div>
            <div id="outer">
                <audio id="dictVoice" style="display: none"></audio>
            </div>
            """.format('collins' if single_dict == 'collins_eng' else single_dict, result.decode('utf-8'))

            if single_dict != "collins_eng":
                return html

            # For collins_eng
            def replace_chinese_tag(soup):
                tags = []
                assert isinstance(soup, (Tag, NavigableString))
                try:
                    children = list(soup.children)
                except AttributeError:
                    children = []
                if children.__len__() > 1:
                    for tag in children:
                        if not isinstance(tag, (Tag, NavigableString)):
                            continue
                        tags.extend(replace_chinese_tag(tag))
                else:
                    match = re.search("[\u4e00-\u9fa5]", soup.text if isinstance(soup, Tag) else str(soup))
                    try:
                        has_title_attr = 'title' in soup.attrs
                    except AttributeError:
                        has_title_attr = False
                    if not match or has_title_attr:
                        if has_title_attr:
                            soup.string = soup['title']
                        if re.match("(\s+)?\d{1,2}\.(\s+)?", soup.string if soup.string else ""):
                            p_tag = Tag(name="p")
                            p_tag.insert(0, Tag(name="br"))
                            tags.append(p_tag)
                        tags.append(soup)
                    else:
                        if match:
                            hanzi_pos = soup.string.find(match.group(0))
                            if hanzi_pos >= 5:
                                soup = soup.string[:hanzi_pos]
                                tags.append(soup)
                return tags

            if len(result.decode('utf-8')) <= 40:  # 32
                return self._get_singledict('ee')['result']
            bs = BeautifulSoup(html)
            ul_tag = bs.find("ul")
            ul_html = BeautifulSoup("".join([str(tag) for tag in replace_chinese_tag(ul_tag)]))
            bs.ul.replace_with(ul_html)
            return bs.prettify()

        except:
            return ''

    @export(u'柯林斯英英', 17)
    def fld_collins_eng(self):
        return self._get_singledict('collins_eng')

    @export(u'英式发音', 2)
    def fld_british_audio(self):
        audio_url = u'https://dict.youdao.com/dictvoice?audio={}&type=1'.format(
            self.word)
        if youdao_download_mp3:
            filename = u'_youdao_{}_uk.mp3'.format(self.word)
            if self.download(audio_url, filename):
                return self.get_anki_label(filename, 'audio')
        return audio_url

    @export(u'美式发音', 3)
    def fld_american_audio(self):
        audio_url = u'https://dict.youdao.com/dictvoice?audio={}&type=2'.format(
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

    @export(u'美式发音', 3)
    def fld_american_audio(self):
        audio_url = u'https://dict.youdao.com/dictvoice?audio={}&type=2'.format(
            self.word)
        if youdao_download_mp3:
            filename = u'_youdao_{}_us.mp3'.format(self.word)
            if self.download(audio_url, filename):
                return self.get_anki_label(filename, 'audio')
        return audio_url

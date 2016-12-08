#-*- coding:utf-8 -*-
import urllib
import urllib2
import re
from collections import defaultdict
import xml.etree.ElementTree
from .base import Service

youdao_css = '''
    <style type="text/css">
        @charset "utf-8";a,a:active,a:hover{color:#138bff}a{cursor:pointer}body{font-size:14px}.nav-label .nav,.page,.page a{text-align:center}.emphasis,b,h4,h5{font-weight:400}.baike_detail .content,.collins h4 .title,.ec h2 span,.fanyi,strong{word-wrap:break-word}html{-webkit-text-size-adjust:none}.collins h4 .phonetic,.ec .phonetic{font-family:lucida sans unicode,arial,sans-serif}h1,h2,h3,h4,h5,input,li,ol,p,textarea,ul{margin:0;padding:0;outline:0}li,ol,ul{list-style:none}a{text-decoration:none}strong{color:#c50000}#bd{padding:7px 0;background:#f4f4f4}.p-index_entry #bd{padding:0;background:#fff}.p-index #hd{border-bottom:1px solid #e8e8e8}.content-wrp{margin:7px}#ft{padding:7px 0;background:#fff}.empty-content{padding:35px 7px;background:#fff;vertical-align:middle}#dictNav,#dictNavList{position:absolute;right:7px}.dict-dl{font-size:9pt}.page{display:block;border:1px solid #e1e1e1;border-radius:2px;background:#fff;color:#313131;-o-border-radius:2px}.page a{display:inline-block;padding:11px 0;width:49%}.dict_sents_result .col3,.source{text-align:right}.dict-container{background:#fff}.dict-container h4{padding:0 7px;border-bottom:1px solid #e1e1e1}.dict-container .trans-container{padding:7px}.dict-container .trans-title{display:block;padding:7px 0;color:#313131}.dict-dl{display:block;padding:7px;border:1px solid #e1e1e1;background-color:#fafafa}.core,.secondary,.secondaryFont{font-size:15px}#dictNav{top:350px;-webkit-transition:top .3s;transition:top .3s}#dictNavBtn{display:inline-block;overflow:hidden;padding-top:3pc;width:3pc;height:0;background:url(http://shared.ydstatic.com/dict/youdaowap/changeImg/dict_unfold_icon_normal.png) no-repeat;background-size:100%}#dictNavBtn.selected{background:url(http://shared.ydstatic.com/dict/youdaowap/changeImg/dict_unfold_icon_pressed.png) no-repeat;background-size:100%}#dictNavList{bottom:49px;display:none;overflow-y:scroll;width:200px;height:0;background:rgba(0,0,0,.7);-webkit-transition:height .5s}#dictNavList li{padding:7px 0;border-bottom:1px solid hsla(0,0%,100%,.3)}#dictNavList li a{display:inline-block;box-sizing:border-box;padding:0 7px;width:100%;color:#fff}.core,body{color:#4e4c4a}h2{margin:0;padding:0}.secondary{color:#847965}.emphasis,b{color:#9c0;font-style:italic}.clickable{color:#279aec}.grey{color:#847965}.serial{margin-right:.7em}.source{padding-top:.7em}.mcols-layout{overflow:hidden}.mcols-layout .col1{float:left;width:1.33em}.mcols-layout .col2{overflow:auto}.mcols-layout .col3{float:right;vertical-align:top}a.pronounce{display:inline-block;width:24px;height:24px;background-image:url(http://shared.ydstatic.com/dict/youdaowap/icon/dict_pronounce-_icon_normal.png);background-size:24px 24px;text-indent:-9999px;font-size:0}a.pronounce:active{background-image:url(http://shared.ydstatic.com/dict/youdaowap/icon/dict_pronounce-_icon_pressed.png)}a.pronounce.disbled{background-image:url(http://shared.ydstatic.com/dict/youdaowap/icon/dict_pronounce-_icon_disable.png)}.ec a.pronounce{vertical-align:middle}.dict-container .trans-container h4{padding:0;border:none;-webkit-tap-highlight-color:rgb(255,255,0)}.dict-container .dict_sents_result{padding:0}.dict-container .dict_sents_result .content{padding:7px}.dict_sents_result .clickable{font-size:13px}.dict_sents_result li{padding-top:.6em}.dict_sents_result li:first-child{padding-top:0}.dict_sents_result .speech-size{margin-top:-10px}.dict_sents_result .more-sents{display:block;padding:7px}.collins .star{display:inline-block;overflow:hidden;margin:0 7px;width:77px;height:13px;background:url(http://shared.ydstatic.com/dict/youdaowap/icon/dict_star_live.png);background-size:77px 13px}.collins .star1{width:14px}.collins .star2{width:28px}.collins .star3{width:45px}.collins .star4{width:61px}.collins .star5{width:77px}.cj .colExam,.ck .colExam,.jc .colExam,.kc .colExam{width:3em}.collins .per-collins-entry li{padding:.6em 0 0}.collins li .mcols-layout{padding:.4em 0 0}.collins h4 .title{overflow:hidden}.ec h2{margin-bottom:.7em;font-size:1pc;line-height:1.5em}.ec h2 .amend{float:right;text-decoration:underline}.ec h2 span{display:inline-block}.ec .sub{margin-top:.7em;padding-top:.7em}.ec .core{padding-left:.33em}.web_trans .webPhrase{margin-top:.6em}.web_trans .trans-list>li{padding:.6em 0 0}.web_trans .trans-list>li:first-child{padding-top:0}ce_new .trans-list li{padding:.7em 0 0}.ce_new .source,.ce_new>ul .per-tran{padding:.7em 0}.ce_new>ul .per-tran:first-child{border:none}.cj>ul,.ck>ul{padding-bottom:.7em}.cj h4{font-weight:700}.cj .grey{font-weight:400}.cj>h4{padding-top:.7em}.cj>h4:first-child{padding-top:0}.ck>h4{padding-top:.7em}.ck>h4:first-child{padding-top:0}.ec21 .phrs,.ec21 .posType>li,.ec21 .source,.ec21 .wfs,.ee>ul>li{padding:.7em 0}.ec21 ins{margin:0 .5em;color:#b6afa2;text-decoration:none}.ec21 .serial{margin-right:.7em}.ee .per-tran,.hh>ul li{padding:.3em 0}.ee>ul{margin-top:.7em}.fanyi{overflow:hidden}.hh>h4{padding-top:.7em}.hh>h4:first-child{padding-top:0}.hh .source{padding:.7em 0}.jc h4{font-weight:700}.jc .origin,.jc sup{font-weight:400}.jc .origin{font-size:.86em}.kc h4{font-weight:700}.loading{padding:2em;color:#4e4c4a}.rel_word>ul li{padding:.3em 0}.rel_word>ul li:first-child{padding-top:0}.special>ul>li{padding:.7em 0}.special>ul>li:first-child{padding-top:0}.special .source{padding:.7em 0}.syno>ul li{padding:.3em 0}.syno>ul li:first-child{padding-top:0}.baike .target{position:relative;display:block;padding-right:40px}.baike .source,.baike>ul li{padding:.7em 0}.baike>ul li:first-child{padding-top:0}.typo .clickable{margin-right:7px}.typo li{padding:7px 0 0}.baike_detail>h4{padding:0 0 .5em;font-size:24px}.baike_detail li{padding:.5em 0}.baike_detail p{margin-bottom:.5em}.baike_detail p:first-child{padding-bottom:.5em}.baike_detail .grey{display:block;padding:.8em 0}.baike_detail .img{clear:both;display:block;overflow:hidden;width:auto!important;font-weight:400;font-size:9pt;line-height:18px}.baike_detail .img_r{float:right;margin-left:1em}.baike_detail img{width:88px;height:auto;-webkit-border-radius:3px}.baike_detail .img strong{display:none}.baike_detail strong{display:block;padding:.5em 0}.baike_detail a,.baike_detail a b{color:#279aec}</style>
'''


def with_css(css):
    def _with(fld_func):
        def _deco(cls, word, single_dict):
            div_wrapper = '<div id="%s_contentWrp" class="content-wrp dict-container"><div id="%s" class="trans-container %s ">%s</div></div>'
            return css + div_wrapper % (single_dict, single_dict, single_dict, fld_func(cls, word, single_dict))
        return _deco
    return _with


def label(label):
    def _with(fld_func):
        def _deco(cls, word):
            fld_func.export_fld_label = tag
        return _deco
    return _with


class Youdao(Service):

    def __init__(self):
        self.cache = defaultdict(str)

    @property
    def fields(self):
        return [dict(label=u'音标', action=self.fld_phonetic),
                dict(label=u'基本释义', action=self.fld_explains),
                dict(label=u'柯林斯英汉', action=self.fld_collins),
                dict(label=u'21世纪', action=self.fld_ec21),
                dict(label=u'英英释义', action=self.fld_ee),
                dict(label=u'网络释义', action=self.fld_web_trans),
                dict(label=u'同根词', action=self.fld_rel_word),
                dict(label=u'同近义词', action=self.fld_syno),
                dict(label=u'双语例句', action=self.fld_blng_sents_part),
                dict(label=u'权威例句', action=self.fld_auth_sents_part),
                dict(label=u'百科', action=self.fld_baike),
                dict(label=u'新英汉大辞典(中)', action=self.fld_ce_new),
                dict(label=u'汉语词典(中)', action=self.fld_hh),
                dict(label=u'专业释义(中)', action=self.fld_special),
                dict(label=u'原生例句', action=self.fld_media_sents_part),
                ]

    def _get_from_api(self, word, lang='eng'):
        url = "http://dict.youdao.com/fsearch?client=deskdict&keyfrom=chrome.extension&pos=-1&doctype=xml&xmlVersion=3.2&dogVersion=1.0&vendor=unknown&appVer=3.1.17.4208&le=%s&q=%s" % (
            lang, word)
        phonetics, explains = '', ''
        try:
            result = urllib2.urlopen(url, timeout=5).read()
            # showInfo(str(result))
            doc = xml.etree.ElementTree.fromstring(result)
            # fetch symbols
            symbol, uk_symbol, us_symbol = doc.findtext(".//phonetic-symbol"), doc.findtext(
                ".//uk-phonetic-symbol"), doc.findtext(".//us-phonetic-symbol")
            if uk_symbol and us_symbol:
                phonetics = 'UK [%s] US [%s]' % (uk_symbol, us_symbol)
            elif symbol:
                phonetics = '[%s]' % symbol
            else:
                phonetics = ''
            # fetch explanations
            explains = '<br>'.join([node.text for node in doc.findall(
                ".//custom-translation/translation/content")])
        except:
            pass
        finally:
            result = {'phonetic': phonetics, 'explains': explains}
            if phonetics or explains:
                self.cache[word] = result
            return result

    @label(u'音标')
    def export_fld_phonetic(self, word):
        if word in self.cache:
            return self.cache[word]['phonetic']
        else:
            return self._get_from_api(word)['phonetic']

    @label(u'基本释义')
    def export_fld_explains(self, word):
        if word in self.cache:
            return self.cache[word]['explains']
        else:
            return self._get_from_api(word)['explains']

    @with_css(youdao_css)
    def _get_singledict(self, word, single_dict, lang='eng'):
        url = "http://m.youdao.com/singledict?q=%s&dict=%s&le=%s&more=false" % (
            word, single_dict, 'eng')
        try:
            result = urllib2.urlopen(url, timeout=5).read()
            return result
        except:
            return ''

    @label(u'柯林斯英汉')
    def export_fld_collins(self, word):
        return self._get_singledict(word, 'collins')

    @label(u'21世纪')
    def export_fld_ec21(self, word):
        return self._get_singledict(word, 'ec21')

    @label(u'英英释义')
    def export_fld_ee(self, word):
        return self._get_singledict(word, 'ee')

    @label(u'网络释义')
    def export_fld_web_trans(self, word):
        return self._get_singledict(word, 'web_trans')

    @label(u'同根词')
    def export_fld_rel_word(self, word):
        return self._get_singledict(word, 'rel_word')

    @label(u'同近义词')
    def export_fld_syno(self, word):
        return self._get_singledict(word, 'syno')

    @label(u'双语例句')
    def export_fld_blng_sents_part(self, word):
        return self._get_singledict(word, 'blng_sents_part')

    @label(u'原生例句')
    def export_fld_media_sents_part(self, word):
        return self._get_singledict(word, 'media_sents_part')

    @label(u'权威例句')
    def export_fld_auth_sents_part(self, word):
        return self._get_singledict(word, 'auth_sents_part')

    @label(u'新英汉大辞典(中)')
    def export_fld_ce_new(self, word):
        return self._get_singledict(word, 'ce_new')

    @label(u'百科')
    def export_fld_baike(self, word):
        return self._get_singledict(word, 'baike')

    @label(u'汉语词典(中)')
    def export_fld_hh(self, word):
        return self._get_singledict(word, 'hh')

    @label(u'专业释义(中)')
    def export_fld_special(self, word):
        return self._get_singledict(word, 'special')

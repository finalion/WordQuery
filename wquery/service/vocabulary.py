#-*- coding:utf-8 -*-
import urllib
import urllib2
import re
from collections import defaultdict
from .base import export, with_styles
from .webservice import WebService
from aqt.utils import showInfo

css = '''
    <style type="text/css">
@charset "UTF-8";body.with-light-header.with-tab-dictionary header.page-header.fixed{background-color:rgba(39,72,102,.95)}.wordPage .main{width:50%;float:left;clear:left}.wordPage{margin:0 auto;position:relative;font-family:'Open Sans';font-size:15px;padding-top:0}.wordPage .section{margin-bottom:1em}.wordPage:after{content:".";display:block;height:0;clear:both;visibility:hidden}.wordPage .related{float:right;width:45%;min-width:336px;clear:right}.wordPage .blurb{color:#444;overflow:hidden}.wordPage .blurb .long{line-height:175%;margin:.5em 0}.wordPage .blurb .short i:first-of-type{color:#438007;font-style:normal}.wordPage .blurb .short{font-size:1.8em;margin-top:0;margin-bottom:.5em;font-weight:300}.wordPage .definition .sectionHeader .word{display:block;font-weight:300;font-size:2em}.wordPage .definition .sectionHeader{margin-bottom:.25em}.wordPage h1{margin:0 0 10px 0;letter-spacing:0;font-size:8em;text-transform:none;color:black;font-weight:300;display:block;width:100%;display:block;white-space:nowrap}.wordHeader{position:relative;overflow:hidden}.definitionNavigator{margin:0 0 20px 0;padding:0;width:100%;position:relative}.definitionNavigator td{vertical-align:top}.definitionNavigator .groupNumber{color:#282828;line-height:20px;font-weight:normal;padding:.75em 10px 0 0;font-size:12px;text-align:center}.definitionNavigator td.posList{padding:7px 0;width:1%}.definitionNavigator .def{display:block;font-size:.85em;padding:.5em 5px}.definitionNavigator .def.selected{display:block}.definitionNavigator a{text-decoration:none;padding:1px 6px 2px 5px;margin:0 3px 0 0;font-size:12px;color:white;font-weight:normal;font-style:italic;-ms-filter:"alpha(opacity=30)";filter:alpha(opacity=30);opacity:.3;border-radius:4px}.definitionNavigator a.selected{color:white;opacity:1;-ms-filter:"alpha(opacity=100)";filter:alpha(opacity=100)}.definitionNavigator a.pos_n{background-color:#e3412f}.definitionNavigator a.pos_v{background-color:#539007}.definitionNavigator a.pos_a{background-color:#f8b002}.definitionNavigator a.pos_r{background-color:#684b9d}.definitionNavigator a.pos_n.selected{background-color:#e3412f}.definitionNavigator a.pos_v.selected{background-color:#539007}.definitionNavigator a.pos_a.selected{background-color:#f8b002}.definitionNavigator a.pos_r.selected{background-color:#684b9d}a.anchor{text-decoration:none;padding:0 6px 0 6px;font-size:.75em;color:white;line-height:21px;font-style:italic;position:absolute;top:.8em;left:13px;display:block;border-radius:4px;min-width:21px;text-align:center}.pos_n a.anchor{background-color:#e3412f}.pos_v a.anchor{background-color:#539007}.pos_a a.anchor{background-color:#f8b002}.pos_r a.anchor{background-color:#684b9d}.wordPage ol.senses .definition{font-weight:bold}.wordPage .example{font-style:italic;color:#666;margin:1em;font-size:1.1em;font-weight:300}.wordPage .example strong{font-weight:normal}.wordPage #wordFamilies{position:relative;z-index:1;padding:10px 0}.wordPage .definition h2{margin:0;font-size:16px;padding:2px 0 10px 0}.wordPage .definition h2 i{color:#22558a}.wordPage .definition h3{font-size:1.1em;font-weight:normal;margin:0;color:#333;margin:0;padding:.5em 15px .5em 60px;border-bottom:1px solid #ddd;border-top:1px solid #ddd}.wordPage .definition .sord1 h3{border-top:0}.wordPage .definition h3 .pos,.stackPane h3 .pos{font-style:italic;color:#666}.wordPage .definition .pos .examples{color:#999;border-bottom:1px dashed #999;padding:4px 0 4px 0}.wordPage .definition .pos .linkedwords{margin-bottom:1em;padding:4px 0 4px 0;border-bottom:1px solid #999}.wordPage .definition .group{position:relative;margin-top:3em;margin-bottom:3em;border-top:3px solid #666}.wordPage .definition .ordinal{margin-bottom:10px;background-color:#f5f5f5;border-top:1px solid black}.wordPage .definition .ordinal.first{border-top:0;margin-top:1px}.wordPage .definition .group .groupNumber:after{content:'.'}.wordPage .definition .group .groupNumber{position:absolute;color:black;width:25px;height:25px;line-height:25px;font-weight:300;font-size:1.5em;padding:0;text-align:center;top:-1.4em;left:0}.wordPage .definition .sense{clear:left;position:relative;overflow:hidden}.collapsed .defContent{display:none}.wordPage .definition .pos .sense .pointers .pointertype{color:#999}.wordPage .definition .pos .sense .pointers .pointer{margin-left:10px}.wordPage .definition .pos .sense .pointers .pointer .definition{margin-left:10px}.wordPage .definition .pos .sense .pointers .pointer .examples{margin-left:10px}.wordPage .definition .pos .sense .pointers .pointer .linkedwords{margin-left:10px}.wordPage .definition dd{margin:1em 0}.wordPage .definition .sense dl dd .definition{font-size:90%;font-weight:300;background-image:none;padding:0 5px 0 0;margin:.25em 0}.wordPage .definition .sense h4{display:inline;margin:0;font-size:90%}.wordPage .definition .sense dl{margin:.5em 0}
.wordPage .definition dl{position:relative}.wordPage .definition dd{padding-left:90px;padding-right:15px}.wordPage .definition dt{width:70px;color:#666;font-size:.75em;font-weight:300;float:left;margin-left:15px;padding-top:.25em}.wordPage .definition dl.expanded .less{display:block}.wordPage .definition dl.expanded .more{display:none}.wordPage .definition dd.less{display:none}.wordPage .definition dd .expander{font-style:italic;font-size:90%}.wordPage .definition .similar .word{display:block;padding-left:10px;height:60px;width:100%;line-height:60px;border-bottom:1px solid #dcdcdc;box-sizing:border-box;-ms-box-sizing:border-box;-moz-box-sizing:border-box;-webkit-box-sizing:border-box;position:relative}.wordPage .definition .similar .thumb{background-repeat:no-repeat;background-position:50% 50%;width:100px;height:59px;position:absolute;top:0;right:0}.sectionHeader.progress{margin-bottom:0}.wordforms td{border:0}.wordforms td.posList{white-space:nowrap;padding-right:5px}.wordforms td.posList.nodefs{width:auto}.wordforms .definitionNavigator a.pos{font-size:11px;line-height:17px;margin:0 10px 5px 0;display:inline-block;border-radius:4px}.wordforms .definitionNavigator .def{font-size:.85em;font-weight:normal;padding-left:0}.wordforms .variant{padding:0 0 5px 0}.wordforms h4.alternatespellings{font-size:11px;margin:5px 0 5px 0}.wordforms table.wordregion{border-collapse:collapse}.wordforms .variant a.word{position:relative;color:#22558a;text-decoration:underline;opacity:1;font-style:normal;font-weight:normal;margin:0;padding:0}.wordforms .variant .region{position:relative;top:2px;margin:0 4px 0 0}.wordforms .definitionNavigator a.listen{padding:0;opacity:1;cursor:pointer}.wordforms .definitionNavigator a.listen:hover:before{color:#666}.wordforms .definitionNavigator a.listen:before{text-decoration:none;color:#999;font-family:"SSStandard";display:inline;content:'🔊';font-style:normal;font-weight:normal}.wordforms table.wordregion td{padding:0 6px 5px 0}.wordforms .listen .audioidx{font-size:8px;color:#666;vertical-align:baseline;padding-left:2px}.vcom_wordfamily{position:relative;display:block}.vcom_wordfamily ul{display:block;position:relative;list-style:none;margin:0;padding:5px 0 10px 0;overflow:hidden}.vcom_wordfamily ul:after{content:'';clear:both;height:0;width:100%}.vcom_wordfamily li{margin:0;padding:0;display:block}.vcom_wordfamily li .row{display:table;width:100%}.vcom_wordfamily canvas{display:block;width:100%;margin:1px 0}.vcom_wordfamily .bar{background-color:#ccc;border-left:1px solid white;height:10px;position:relative;vertical-align:top;display:table-cell;cursor:pointer;margin:0}.vcom_wordfamily .bar:FIRST-CHILD{border-left:none}.vcom_wordfamily .bar span{position:absolute;top:50%;left:50%;margin-top:-.8em;display:block;font-size:11px;background-color:white;border-radius:3px;padding:0 6px;line-height:190%;z-index:1;color:#333;box-shadow:0 0 3px 0 rgba(0,0,0,0.65);white-space:nowrap}.vcom_wordfamily .tooltip{width:270px;border-radius:5px;position:absolute;background-color:rgba(26,58,91,0.95);z-index:1;color:white;box-shadow:0 0 3px 0 rgba(0,0,0,0.45);padding:1em;font-size:.9em}.vcom_wordfamily .bar:hover:after{content:'';position:absolute;left:50%;margin-left:-6px;top:-10px;width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-top:6px solid rgba(40,52,69,0.79)}.vcom_wordfamily .tooltip h3{margin:0 0 .5em 0;color:white;font-size:1.3em}.vcom_wordfamily .tooltip p{margin:0;line-height:150%;font-weight:300}.vcom_wordfamily .bar:hover{background-color:#4275aa}.vcom_wordfamily .bar.selected:hover{background-color:#22558a}.vcom_wordfamily .bar.selected{background-color:#22558a}body.with-tab-dictionary .fixed-tray .banner{color:white;top:0;position:absolute;width:100%;opacity:0;visibility:hidden;z-index:1;text-align:center;height:300px;background:linear-gradient(#33526d 0,rgba(32,67,98,0.2) 30%,rgba(0,0,0,0.41) 90%),url('/images/dictionary/header2-1nt6bys.jpg');background-repeat:no-repeat,no-repeat;background-size:cover,cover;background-position:50% 50%,40% 100%;-webkit-transition:.5s all;-moz-transition:.5s all;-o-transition:.5s all;-ms-transition:.5s all;transition:.5s all}body.with-tab-dictionary.dict-home .fixed-tray .banner{opacity:1;visibility:visible}body.with-tab-dictionary.list-builder-open .fixed-tray .banner,body.with-tab-dictionary.ac-open .fixed-tray .banner,body.with-tab-dictionary.advsearch-open .fixed-tray .banner{opacity:0;visibility:hidden}body.with-tab-dictionary.dict-home .fixed-tray .banner>.wrapper{position:absolute;bottom:0;width:100%;padding:0 0 2em 0}body.with-tab-dictionary .fixed-tray .banner h1{margin:0}body.with-tab-dictionary .fixed-tray .banner h2{font-size:1.2em;line-height:1em;margin:.25em 0 0 0}body.with-tab-dictionary .fixed-tray{background:-webkit-linear-gradient(#204362 0,#33526d 100%);background:-moz-linear-gradient(#33526d 0,#204362 100%);background:-ms-linear-gradient(#33526d 0,#204362 100%);background:gradient(#33526d 0,#204362 100%)}</style>
'''
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


class Vocabulary(WebService):

    __register_label__ = u'vocabulary.com'

    def __init__(self):
        super(Vocabulary, self).__init__()
        self.cache = defaultdict(defaultdict)

    def _get_content(self):
        url = "https://www.vocabulary.com/dictionary/definition.ajax?search=%s" % self.word
        try:
            result = urllib2.urlopen(url, timeout=5).read()
            self.cache[self.word] = {'short': '', 'long': '',
                                     'primary': '', 'full': ''}
            m = re.search('(<p class="short">.*?</p>)', result)
            if m:
                self.cache[self.word]['short'] = m.groups()[0]
            m = re.search('(<p class="long">.*?</p>)', result)
            if m:
                self.cache[self.word]['long'] = m.groups()[0]
            m = re.search(
                '(<table class="definitionNavigator".*?</table>)', result, re.DOTALL)
            if m:
                self.cache[self.word][
                    'primary'] = '<div class="wordPage vocab blurbed clearfloat content-wrapper"><div class="section definition">' + m.groups()[0] + '</div></div>'
            m = re.findall(
                '(<!-- BEGIN GROUP --><div class="group">.*?</div><!-- END GROUP -->)', result, re.DOTALL)
            if m:
                self.cache[self.word][
                    'full'] = '<div class="wordPage vocab blurbed clearfloat content-wrapper"><div class="section definition">' + ''.join(m) + '</div></div>'
        except Exception as e:
            showInfo(str(e))
            pass

    @export(u'Short Description', 2)
    def fld_short_desc(self):
        if self.word not in self.cache or not self.cache[self.word].has_key('short'):
            self._get_content()
        return self.cache[self.word]['short']

    @export(u'Long Description', 3)
    def fld_long_desc(self):
        if self.word not in self.cache or not self.cache[self.word].has_key('long'):
            self._get_content()
        return self.cache[self.word]['long']

    @export(u'Primary Meanings', 4)
    @with_styles(css=css)
    def fld_primary_meanings(self):
        if self.word not in self.cache or not self.cache[self.word].has_key('primary'):
            self._get_content()
        return self.cache[self.word]['primary']

    @with_styles(css=css)
    @export(u'Full Definitions', 5)
    def fld_full_definitions(self):
        if self.word not in self.cache or not self.cache[self.word].has_key('full'):
            self._get_content()
        return self.cache[self.word]['full']

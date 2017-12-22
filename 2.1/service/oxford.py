from warnings import filterwarnings

from bs4 import BeautifulSoup, Tag
from requests import Session

filterwarnings('ignore')

try:
    import urllib2
except:
    import urllib.request as urllib2
import json
from .base import WebService, export, register, with_styles


@register("Oxford")
class Oxford(WebService):

    def __init__(self):
        super(Oxford, self).__init__()

    def _get_from_api(self, lang="en"):
        word = self.word
        baseurl = "https://od-api.oxforddictionaries.com/api/v1"
        app_id = "45aecf84"
        app_key = "bb36fd6a1259e5baf8df6110a2f7fc8f"
        headers = {"app_id": app_id, "app_key": app_key}

        word_id = urllib2.quote(word.lower().replace(" ", "_"))
        url = baseurl + "/entries/" + lang + "/" + word_id
        url = urllib2.Request(url, headers=headers)
        response = json.loads(urllib2.urlopen(url).read())

        return response["results"]

    @export("Lexical Category", 1)
    def _fld_category(self):
        return self._get_from_api()[0]["lexicalEntries"][0]["lexicalCategory"]


@register(u'牛津学习词典')
class OxfordLearning(WebService):
    _base_url = 'https://www.oxfordlearnersdictionaries.com/definition/english/'

    def __init__(self):
        super(OxfordLearning, self).__init__()

        self.s = Session()
        self.s.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/31.0.1623.0 Safari/537.36'
        }
        self.s.get(self._base_url)

    def query(self, word):
        """

        :param word:
        :rtype:  WebWord
        """
        _qry_url = self._base_url + word
        rsp = self.s.get(_qry_url, )
        if rsp.status_code == 200:
            return OxfordLearningDictWord(rsp.content.decode('utf-8'))

    def _get_single_dict(self, single_dict):
        if not (self.cached(single_dict) and self.cache_result(single_dict)):
            web_word = self.query(self.word)
            if web_word:
                self.cache_this(
                    {
                        'phonetic': '{} {}'.format(web_word.wd_phon_bre, web_word.wd_phon_nam),
                        'pos': web_word.wd_pos,
                        'ee': ''.join(web_word.definitions_html),
                        's_bre': web_word.wd_sound_url_bre,
                        's_ame': web_word.wd_sound_url_nam,
                    }
                )
            else:
                self.cache_this(
                    {
                        'phonetic': '',
                        'pos': '',
                        'ee': '',
                        's_bre': '',
                        's_ame': '',
                    }
                )
        return self.cache_result(single_dict)

    @export(u'音标', 0)
    def phonetic(self):
        return self._get_single_dict('phonetic')

    @export(u'词性', 1)
    def pos(self):
        return self._get_single_dict('pos')

    @export(u'释义', 2)
    @with_styles(cssfile='_oxford.css')
    def ee(self):
        return '<div style="margin-left: 20px">' + self._get_single_dict(
            'ee') + "</div>" if "<li>" not in self._get_single_dict('ee') else self._get_single_dict('ee')

    def get_sound_bre(self):
        url = self._get_single_dict('s_bre')
        filename = u'_oxford_{}_uk.mp3'.format(self.word)
        if url and self.download(url, filename):
            return self.get_anki_label(filename, 'audio')
        return ''

    def get_sound_ame(self):
        url = self._get_single_dict('s_nam')
        filename = u'_oxford_{}_us.mp3'.format(self.word)
        if url and self.download(url, filename):
            return self.get_anki_label(filename, 'audio')
        return ''

    @export(u'英式发音', 3)
    def sound_bre(self):
        return self.get_sound_bre()

    @export(u'美式发音', 4)
    def sound_ame(self):
        return self.get_sound_ame()

    @export(u'英式发音优先', 5)
    def sound_pri(self):
        bre = self.get_sound_bre()
        return bre if bre else self.get_sound_ame()


class OxfordLearningDictWord:

    def __init__(self, markups):
        if not markups:
            return
        self.markups = markups
        self.bs = BeautifulSoup(self.markups)
        self._defs = None
        self._defs_html = None

    @staticmethod
    def _cls_dic(class_nm):
        return {'class': class_nm}

    # region Tags
    @property
    def tag_web_top(self):
        """

        word - class: h
        pos - class: pos

        :rtype: Tag
        """
        return self.bs.find("div", self._cls_dic('webtop-g'))

    @property
    def tag_pron(self):
        """

        :rtype: Tag
        """
        return self.bs.find("div", self._cls_dic('pron-gs ei-g'))

    @property
    def tag_phon_bre(self):
        """

        :rtype: Tag
        """
        return self.tag_pron.find('span', self._cls_dic('pron-g'), geo='br')

    @property
    def tag_phon_nam(self):
        """

        :rtype: Tag
        """
        return self.tag_pron.find('span', self._cls_dic('pron-g'), geo='n_am')

    # ---- Explains
    @property
    def tag_explain(self):
        """

        :rtype: Tag
        """
        return self.bs.find('span', self._cls_dic('sn-gs'))

    # endregion

    @property
    def wd_phon_bre(self):
        """

        :return: pre_fix, phon
        """
        _tag_phn = self.tag_phon_bre.find('span', self._cls_dic('phon')).contents[3]
        return "{} {}".format(
            self.tag_phon_bre.find('span', self._cls_dic('prefix')).string,
            '/{}/'.format(_tag_phn.text if isinstance(_tag_phn, Tag) else _tag_phn)
        )

    @property
    def wd_pos(self):
        try:
            return self.tag_web_top.find("span", 'pos').text
        except:
            return ''

    @property
    def wd_phon_nam(self):
        """

        :return: pre_fix, phon
        """
        _tag_phn = self.tag_phon_nam.find('span', self._cls_dic('phon')).contents[3]
        return "{} {}".format(
            self.tag_phon_nam.find('span', self._cls_dic('prefix')).string,
            '/{}/'.format(_tag_phn.text if isinstance(_tag_phn, Tag) else _tag_phn)
        )

    @property
    def wd_sound_url_bre(self):
        try:
            return self.tag_phon_bre.find('div', self._cls_dic('sound audio_play_button pron-uk icon-audio'))[
                'data-src-mp3']
        except:
            return ''

    @property
    def wd_sound_url_nam(self):
        try:
            return self.tag_phon_bre.find('div', self._cls_dic('sound audio_play_button pron-us icon-audio'))[
                'data-src-mp3']
        except:
            return ''

    def get_definitions(self):
        if not self._defs:
            defs = []
            defs_html = []
            tag_exp = self._clean(self.tag_explain)
            lis = [li for li in tag_exp.find_all('li')]
            if not lis:
                defs_html.append(str(tag_exp))
                defs.append(tag_exp.text)

            else:
                for li in lis:
                    defs_html.append(str(tag_exp))
                    defs.append(li.text)
            self._defs = defs
            self._defs_html = defs_html
        return self._defs, self._defs_html

    @property
    def definitions(self):
        return self.get_definitions()[0]

    @property
    def definitions_html(self):
        return self.get_definitions()[1]

    def _clean(self, tg):
        """

        :type tg:Tag
        :return:
        """
        decompose_cls = ['xr-gs', 'sound', 'heading', 'topic', 'collapse', 'oxford3000']

        if tg.attrs and 'class' in tg.attrs:
            for _cls in decompose_cls:
                _tgs = tg.find_all(attrs=self._cls_dic(_cls), recursive=True)
                for _tg in _tgs:
                    _tg.decompose()

        rmv_attrs = ['dpsid', 'id']
        for _attr in rmv_attrs:
            if tg.attrs and _attr in tg.attrs:
                try:
                    tg.attrs = {key: value for key, value in tg.attrs.items()
                                if key not in rmv_attrs}
                except ValueError:
                    pass
                for child in tg.children:
                    if not isinstance(child, Tag):
                        continue

        return tg

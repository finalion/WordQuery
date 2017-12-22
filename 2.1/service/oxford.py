from copy import deepcopy
from warnings import filterwarnings

from bs4 import BeautifulSoup, Tag
from requests import Session

from .base import WebService, export, register, with_styles

filterwarnings('ignore')


@register(u'牛津学习词典')
class Oxford(WebService):
    _base_url = 'https://www.oxfordlearnersdictionaries.com/definition/english/'

    def __init__(self):
        super(Oxford, self).__init__()

        self.s = Session()
        self.s.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/31.0.1623.0 Safari/537.36'
        }
        self.s.get(self._base_url)
        self._web_word = None

    def query(self, word):
        """

        :param word:
        :rtype:  WebWord
        """
        _qry_url = self._base_url + word
        rsp = self.s.get(_qry_url, )
        if rsp.status_code == 200:
            return WebWord(rsp.content.decode('utf-8'))

    @property
    def web_word(self):
        if not self._web_word:
            self._web_word = self.query(self.word)
        return self._web_word

    @export(u'音标', 0)
    def phonetic(self):
        return '{} {}'.format(self.web_word.wd_phon_bre, self.web_word.wd_phon_nam)

    @export(u'词性', 1)
    def pos(self):
        return self.web_word.wd_pos

    @export(u'释义', 2)
    @with_styles(cssfile='_oxford.css')
    def ee(self):
        return '<div style="margin-left: 20px">' + self.web_word.definitions_html +"</div>"

    def get_sound_bre(self):
        url = self.web_word.wd_sound_url_bre
        filename = u'_oxford_{}_uk.mp3'.format(self.word)
        if url and self.download(url, filename):
            return self.get_anki_label(filename, 'audio')
        return ''

    def get_sound_ame(self):
        url = self.web_word.wd_sound_url_nam
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


class WebWord:

    def __init__(self, markups):
        if not markups:
            return
        self.markups = markups
        self.bs = BeautifulSoup(self.markups)
        self.with_html = False
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
            pass

    @property
    def wd_sound_url_nam(self):
        try:
            return self.tag_phon_bre.find('div', self._cls_dic('sound audio_play_button pron-us icon-audio'))[
                'data-src-mp3']
        except:
            pass

    @property
    def definitions(self):
        if self._defs and not self.with_html:
            return self._defs
        if self._defs_html and self.with_html:
            return self._defs_html

        defs = []
        defs_html = []
        tag_exp = self._clean(self.tag_explain)
        lis = [li for li in tag_exp.find_all('li')]
        if not lis:
            if self.with_html:
                defs_html.append(
                    str(tag_exp)
                )
            else:
                defs.append(tag_exp.text)

        else:
            for li in lis:
                if self.with_html:
                    defs_html.append(
                        str(tag_exp)
                    )
                else:
                    defs.append(li.text)
        self._defs = defs
        self._defs_html = defs_html
        return self._defs if not self.with_html else self._defs_html

    @property
    def definitions_html(self):
        _with_html = deepcopy(self.with_html)
        self.with_html = True
        # def_html = """
        # <link type="text/css" rel="stylesheet" href="_oxford.css">
        #
        # <ol class="v-gs">
        #     {}
        # </ol>
        # """.format(''.join(_de for _de in self.definitions))
        def_html = ''.join(_de for _de in self.definitions)
        self.with_html = _with_html
        return def_html

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
                    tg.attrs.pop(_attr)
                except ValueError:
                    pass
                for child in tg.children:
                    if not isinstance(child, Tag):
                        continue

        return tg

# -*- coding: utf-8 -*-
# Copyright: khuang6 <upday7@163.com>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

"""
Project : wq
Created: 12/20/2017
"""
import os
from warnings import filterwarnings

import requests as rq
from bs4 import BeautifulSoup, Tag

from .base import WebService, export, register, with_styles

filterwarnings('ignore')
import sys

reload(sys)
sys.setdefaultencoding('utf8')


@register(u'朗文')
class Longman(WebService):

    def __init__(self):
        super(Longman, self).__init__()

    def _get_singledict(self, single_dict):
        """

        :type word: str
        :return:
        """

        if not (self.cached(single_dict) and self.cache_result(single_dict)):
            rsp = rq.get("https://www.ldoceonline.com/dictionary/{}".format(self.word), headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1623.0 Safari/537.36'
            })

            if rsp.status_code == 200:
                bs = BeautifulSoup(rsp.content.decode('utf-8'), 'html.parser', from_encoding="utf-8")
                # Top Container
                dictlinks = bs.find_all('span', {'class': 'dictlink'})
                body_html = ""

                word_info = {
                }
                ee_ = ''
                for dic_link in dictlinks:
                    assert isinstance(dic_link, Tag)

                    # Remove related Topics Container
                    related_topic_tag = dic_link.find('div', {'class': "topics_container"})
                    if related_topic_tag:
                        related_topic_tag.decompose()

                    # Remove Tail
                    tail_tag = dic_link.find("span", {'class': 'Tail'})
                    if tail_tag:
                        tail_tag.decompose()

                    # Remove SubEntry
                    sub_entries = dic_link.find_all('span', {'class': 'SubEntry'})
                    for sub_entry in sub_entries:
                        sub_entry.decompose()

                    # word elements
                    head_tag = dic_link.find('span', {'class': "Head"})
                    if head_tag and not word_info:
                        try:
                            hyphenation = head_tag.find("span", {'class': 'HYPHENATION'}).string  # Hyphenation
                        except:
                            hyphenation = ''
                        try:
                            pron_codes = "".join(
                                list(head_tag.find("span", {'class': 'PronCodes'}).strings))  # Hyphenation
                        except:
                            pron_codes = ''
                        try:
                            POS = head_tag.find("span", {'class': 'POS'}).string  # Hyphenation
                        except:
                            POS = ''

                        try:
                            Inflections = head_tag.find('span', {'class': 'Inflections'})
                            if Inflections:
                                Inflections = str(Inflections)
                            else:
                                Inflections = ''
                        except:
                            Inflections = ''

                        word_info = {
                            'phonetic': pron_codes,
                            'hyphenation': hyphenation,
                            'pos': POS,
                            'inflections': Inflections,
                        }
                        self.cache_this(word_info)
                    if head_tag:
                        head_tag.decompose()

                    # remove script tag
                    script_tags = dic_link.find_all('script')
                    for t in script_tags:
                        t.decompose()

                    # remove img tag
                    img_tags = dic_link.find_all('img')
                    for t in img_tags:
                        self.cache_this({'img': 'https://www.ldoceonline.com' + t['src']})
                        t.decompose()

                    # remove sound tag
                    am_s_tag = dic_link.find("span", title='Play American pronunciation of {}'.format(self.word))
                    br_s_tag = dic_link.find("span", title='Play British pronunciation of {}'.format(self.word))
                    if am_s_tag:
                        am_s_tag.decompose()
                    if br_s_tag:
                        br_s_tag.decompose()

                    # remove example sound tag
                    emp_s_tags = dic_link.find_all('span', {'class': 'speaker exafile fa fa-volume-up'})
                    for t in emp_s_tags:
                        t.decompose()

                    body_html += str(dic_link)
                    ee_ = body_html
                self.cache_this({
                    'ee': ee_
                })

            else:
                return ''
        return self.cache_result(single_dict)

    @export(u'音标', 2)
    def phonetic(self):
        return self._get_singledict('phonetic')

    @export(u'断字单词', 3)
    def hyphenation(self):
        return self._get_singledict('hyphenation')

    @export(u'词性', 1)
    def pos(self):
        return self._get_singledict('pos')

    @export(u'英英解释', 0)
    @with_styles(cssfile='_longman.css')
    def ee(self):
        return self._get_singledict('ee')

    @export(u'图片', 4)
    def pic(self):
        url = self._get_singledict('img')
        filename = u'longman_img_{}'.format(os.path.basename(url))
        if url and self.download(url, filename):
            return self.get_anki_label(filename, 'img')
        return ''

    @export(u'变形', 5)
    @with_styles(cssfile='_longman.css')
    def inflections(self):
        return self._get_singledict('inflections')

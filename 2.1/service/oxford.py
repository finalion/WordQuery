#-*- coding:utf-8 -*-
try:
    import urllib2
except:
    import urllib.request as urllib2
import json
from aqt.utils import showInfo
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

#-*- coding:utf-8 -*-
import json
import re
import urllib

from aqt.utils import showInfo, showText

from .base import WebService, export, register, with_styles


@register(u'海词迷你词典')
class MiniDict(WebService):

    def __init__(self):
        super(MiniDict, self).__init__()
        self.encoder = Encoder()

    def get_content(self, token):
        expressions, sentences, variations = [''] * 3

        encoded_word = self.encoder.go(self.word, token)
        data = urllib.urlencode(
            {'q': self.word, 's': 2, 't': encoded_word})
        result = self.get_response(
            "http://dict.cn/ajax/dictcontent.php", data=data)
        if result:
            expressions = json.loads(result).get("e", "")
            sentences = json.loads(result).get("s", "")
            variations = json.loads(result).get("t", "")
            sentences = re.sub('/imgs/audio\.gif', "", sentences)
            self.cache_this(
                {'expressions': expressions, 'sentences': sentences, 'variations': variations})
        return expressions, sentences, variations

    def get_token_phonetic(self):
        result = self.get_response(
            "http://dict.cn/mini.php?q={}".format(self.word))

        page_token, phonetic = '', ''
        mt = re.search('<script>var dict_pagetoken="(.*?)";</script>', result)
        if mt:
            page_token = mt.groups()[0]
        mp = re.search("(<span class='p'>.*?</span>)", result)
        if mp:
            phonetic = mp.groups()[0]
            self.cache_this({'phonetic': phonetic})
        return page_token, phonetic

    @export(u'音标', 0)
    # @with_css('''<style type="text/css">.p {font-family: Lucida Sans Unicode; color: #666699;}</style>''')
    def fld_phonetic(self):
        return self.cache_result('phonetic') if self.cached('phonetic') else self.get_token_phonetic()[1]

    @export(u'基本释义', 1)
    def fld_explains(self):
        if self.cached('expressions'):
            return self.cache_result('expressions')
            # showInfo(u'%s 基本释义cached:\n %s' % (self.word, res))
        else:
            page_token, phonetic = self.get_token_phonetic()
            return self.get_content(page_token)[0]
            # showInfo(u'%s 基本释义获取:\n %s' % (self.word, res))

    @export(u'例句与用法', 2)
    def fld_sentences(self):
        if self.cached('sentences'):
            return self.cache_result('sentences')
            # showInfo(u'%s 基本释义cached:\n %s' % (self.word, res))
        else:
            page_token, phonetic = self.get_token_phonetic()
            return self.get_content(page_token)[1]
            # showInfo(u'%s 基本释义获取:\n %s' % (self.word, res))

    @export(u'词形变化', 3)
    def fld_variations(self):
        if self.cached('variations'):
            return self.cache_result('variations')
            # showInfo(u'%s 基本释义cached:\n %s' % (self.word, res))
        else:
            page_token, phonetic = self.get_token_phonetic()
            return self.get_content(page_token)[2]
            # showInfo(u'%s 基本释义获取:\n %s' % (self.word, res))


class Encoder(object):

    def __init__(self):
        pass

    def rshift(self, val, n):
        s = val >> n if val >= 0 else (val + 0x100000000) >> n
        return s

    def lshift(self, val, n):
        return self.toSigned32(val << n)

    def toSigned32(self, n):
        n = n & 0xffffffff
        return (n ^ 0x80000000) - 0x80000000

    def RotateLeft(self, a, b):
        rshift = self.rshift(a, 32 - b)
        lshift = self.lshift(a, b)
        s = lshift | rshift
        return s

    def AddUnsigned(self, a, b):
        lX8 = a & 0x80000000
        lY8 = b & 0x80000000
        c = a & 0x40000000
        lY4 = b & 0x40000000
        lResult = (a & 0x3FFFFFFF) + (b & 0x3FFFFFFF)
        if c & lY4:
            return self.toSigned32(lResult ^ 0x80000000 ^ lX8 ^ lY8)
        if c | lY4:
            if lResult & 0x40000000:
                return self.toSigned32(lResult ^ 0xC0000000 ^ lX8 ^ lY8)
            else:
                return self.toSigned32(lResult ^ 0x40000000 ^ lX8 ^ lY8)
        else:
            return self.toSigned32(lResult ^ lX8 ^ lY8)

    def F(self, x, y, z):
        return (x & y) | ((~x) & z)

    def G(self, x, y, z):
        return (x & z) | (y & (~z))

    def H(self, x, y, z):
        return (x ^ y ^ z)

    def I(self, x, y, z):
        return (y ^ (x | (~z)))

    def FF(self, a, b, c, d, x, s, e):
        a = self.AddUnsigned(a, self.AddUnsigned(
            self.AddUnsigned(self.F(b, c, d), x), e))
        return self.toSigned32(self.AddUnsigned(self.RotateLeft(a, s), b))

    def GG(self, a, b, c, d, x, s, e):
        a = self.AddUnsigned(a, self.AddUnsigned(
            self.AddUnsigned(self.G(b, c, d), x), e))
        return self.toSigned32(self.AddUnsigned(self.RotateLeft(a, s), b))

    def HH(self, a, b, c, d, x, s, e):
        a = self.AddUnsigned(a, self.AddUnsigned(
            self.AddUnsigned(self.H(b, c, d), x), e))
        return self.toSigned32(self.AddUnsigned(self.RotateLeft(a, s), b))

    def II(self, a, b, c, d, x, s, e):
        a = self.AddUnsigned(a, self.AddUnsigned(
            self.AddUnsigned(self.I(b, c, d), x), e))
        return self.toSigned32(self.AddUnsigned(self.RotateLeft(a, s), b))

    def ConvertToWordArray(self, a):
        c = len(a)
        d = c + 8
        e = (d - (d % 64)) / 64
        f = (e + 1) * 16
        g = [0] * f  # notice
        h = 0
        i = 0
        while i < c:
            b = (i - (i % 4)) / 4
            h = (i % 4) * 8
            g[b] = (g[b] | self.lshift(ord(a[i]), h))
            i += 1
        b = (i - (i % 4)) / 4
        h = (i % 4) * 8
        g[b] = g[b] | self.lshift(0x80, h)
        g[f - 2] = self.lshift(c, 3)
        g[f - 1] = self.rshift(c, 29)
        return g

    def WordToHex(self, a):
        b = ""
        for lCount in range(0, 4):
            lByte = self.rshift(a, lCount * 8) & 255
            WordToHexValue_temp = "0" + hex(lByte)[2:-1]
            b = b + \
                WordToHexValue_temp[
                    len(WordToHexValue_temp) - 2:len(WordToHexValue_temp)]
        return b

    def Utf8Encode(self, a):
        a = a.replace('\r\n', "\n")
        b = ""
        for n in range(len(a)):
            c = ord(a[n])
            if (c < 128):
                b += unichr(c)
            elif ((c > 127) and (c < 2048)):
                b += unichr((c >> 6) | 192)
                b += unichr((c & 63) | 128)
            else:
                b += unichr((c >> 12) | 224)
                b += unichr(((c >> 6) & 63) | 128)
                b += unichr((c & 63) | 128)
        b += ''.join(map(unichr, [100, 105, 99, 116, 99, 110]))
        if self.pagetoken:
            b += self.pagetoken
        return b

    def go(self, word, pagetoken=None):
        self.word = word
        self.pagetoken = pagetoken
        l = 7
        S12 = 12
        S13 = 17
        S14 = 22
        m = 5
        S22 = 9
        S23 = 14
        S24 = 20
        o = 4
        S32 = 11
        S33 = 16
        S34 = 23
        p = 6
        S42 = 10
        S43 = 15
        S44 = 21
        j = self.Utf8Encode(self.word)
        x = self.ConvertToWordArray(j)
        a = 0x67452301
        b = 0xEFCDAB89
        c = 0x98BADCFE
        d = 0x10325476
        for k in range(0, len(x), 16):
            AA = a
            BB = b
            CC = c
            DD = d
            a = self.FF(a, b, c, d, x[k + 0], l, 0xD76AA478)
            d = self.FF(d, a, b, c, x[k + 1], S12, 0xE8C7B756)
            c = self.FF(c, d, a, b, x[k + 2], S13, 0x242070DB)
            b = self.FF(b, c, d, a, x[k + 3], S14, 0xC1BDCEEE)
            a = self.FF(a, b, c, d, x[k + 4], l, 0xF57C0FAF)
            d = self.FF(d, a, b, c, x[k + 5], S12, 0x4787C62A)
            c = self.FF(c, d, a, b, x[k + 6], S13, 0xA8304613)
            b = self.FF(b, c, d, a, x[k + 7], S14, 0xFD469501)
            a = self.FF(a, b, c, d, x[k + 8], l, 0x698098D8)
            d = self.FF(d, a, b, c, x[k + 9], S12, 0x8B44F7AF)
            c = self.FF(c, d, a, b, x[k + 10], S13, 0xFFFF5BB1)
            b = self.FF(b, c, d, a, x[k + 11], S14, 0x895CD7BE)
            a = self.FF(a, b, c, d, x[k + 12], l, 0x6B901122)
            d = self.FF(d, a, b, c, x[k + 13], S12, 0xFD987193)
            c = self.FF(c, d, a, b, x[k + 14], S13, 0xA679438E)
            b = self.FF(b, c, d, a, x[k + 15], S14, 0x49B40821)
            a = self.GG(a, b, c, d, x[k + 1], m, 0xF61E2562)
            d = self.GG(d, a, b, c, x[k + 6], S22, 0xC040B340)
            c = self.GG(c, d, a, b, x[k + 11], S23, 0x265E5A51)
            b = self.GG(b, c, d, a, x[k + 0], S24, 0xE9B6C7AA)
            a = self.GG(a, b, c, d, x[k + 5], m, 0xD62F105D)
            d = self.GG(d, a, b, c, x[k + 10], S22, 0x2441453)
            c = self.GG(c, d, a, b, x[k + 15], S23, 0xD8A1E681)
            b = self.GG(b, c, d, a, x[k + 4], S24, 0xE7D3FBC8)
            a = self.GG(a, b, c, d, x[k + 9], m, 0x21E1CDE6)
            d = self.GG(d, a, b, c, x[k + 14], S22, 0xC33707D6)
            c = self.GG(c, d, a, b, x[k + 3], S23, 0xF4D50D87)
            b = self.GG(b, c, d, a, x[k + 8], S24, 0x455A14ED)
            a = self.GG(a, b, c, d, x[k + 13], m, 0xA9E3E905)
            d = self.GG(d, a, b, c, x[k + 2], S22, 0xFCEFA3F8)
            c = self.GG(c, d, a, b, x[k + 7], S23, 0x676F02D9)
            b = self.GG(b, c, d, a, x[k + 12], S24, 0x8D2A4C8A)
            a = self.HH(a, b, c, d, x[k + 5], o, 0xFFFA3942)
            d = self.HH(d, a, b, c, x[k + 8], S32, 0x8771F681)
            c = self.HH(c, d, a, b, x[k + 11], S33, 0x6D9D6122)
            b = self.HH(b, c, d, a, x[k + 14], S34, 0xFDE5380C)
            a = self.HH(a, b, c, d, x[k + 1], o, 0xA4BEEA44)
            d = self.HH(d, a, b, c, x[k + 4], S32, 0x4BDECFA9)
            c = self.HH(c, d, a, b, x[k + 7], S33, 0xF6BB4B60)
            b = self.HH(b, c, d, a, x[k + 10], S34, 0xBEBFBC70)
            a = self.HH(a, b, c, d, x[k + 13], o, 0x289B7EC6)
            d = self.HH(d, a, b, c, x[k + 0], S32, 0xEAA127FA)
            c = self.HH(c, d, a, b, x[k + 3], S33, 0xD4EF3085)
            b = self.HH(b, c, d, a, x[k + 6], S34, 0x4881D05)
            a = self.HH(a, b, c, d, x[k + 9], o, 0xD9D4D039)
            d = self.HH(d, a, b, c, x[k + 12], S32, 0xE6DB99E5)
            c = self.HH(c, d, a, b, x[k + 15], S33, 0x1FA27CF8)
            b = self.HH(b, c, d, a, x[k + 2], S34, 0xC4AC5665)
            a = self.II(a, b, c, d, x[k + 0], p, 0xF4292244)
            d = self.II(d, a, b, c, x[k + 7], S42, 0x432AFF97)
            c = self.II(c, d, a, b, x[k + 14], S43, 0xAB9423A7)
            b = self.II(b, c, d, a, x[k + 5], S44, 0xFC93A039)
            a = self.II(a, b, c, d, x[k + 12], p, 0x655B59C3)
            d = self.II(d, a, b, c, x[k + 3], S42, 0x8F0CCC92)
            c = self.II(c, d, a, b, x[k + 10], S43, 0xFFEFF47D)
            b = self.II(b, c, d, a, x[k + 1], S44, 0x85845DD1)
            a = self.II(a, b, c, d, x[k + 8], p, 0x6FA87E4F)
            d = self.II(d, a, b, c, x[k + 15], S42, 0xFE2CE6E0)
            c = self.II(c, d, a, b, x[k + 6], S43, 0xA3014314)
            b = self.II(b, c, d, a, x[k + 13], S44, 0x4E0811A1)
            a = self.II(a, b, c, d, x[k + 4], p, 0xF7537E82)
            d = self.II(d, a, b, c, x[k + 11], S42, 0xBD3AF235)
            c = self.II(c, d, a, b, x[k + 2], S43, 0x2AD7D2BB)
            b = self.II(b, c, d, a, x[k + 9], S44, 0xEB86D391)
            a = self.AddUnsigned(a, AA)
            b = self.AddUnsigned(b, BB)
            c = self.AddUnsigned(c, CC)
            d = self.AddUnsigned(d, DD)
        q = self.WordToHex(a) + self.WordToHex(b) + \
            self.WordToHex(c) + self.WordToHex(d)
        return q.lower()


## [User Guide](README.md) &nbsp;&nbsp;&nbsp;&nbsp;[<u>Develop Guide</u>](develop.md) &nbsp;&nbsp;&nbsp;&nbsp;[Service Shop](shop.md) 


The advanced users can implement new web dictionary services to grab the word explanations, or local dictionary services to extract some certain fields. See [a webservice sample](samples/bing.py) and [a mdxservice sample](samples/LDOCE6.md) for the details.

## WebService

**[Sample](samples/bing.py)**.

### Inherit `WebService` class

```@register(label)``` is used to register the service, and parameter ```label``` as the dictionary name will be shown in the dictioary list.

```python
@register(u'有道词典')
class Youdao(WebService):
    """service implementation"""
```

### Define Dictionary Field

The field export function has to be decorated with ```@export(fld_name, order)```.

- para ```fld_name```: name of the dictionary field

- para ```order```: order of the field, the smaller number will be shown on the upper of the field list.

```python
@export(u'美式音标', 1)
def fld_phonetic_us(self):
    return self._get_field('phonitic_us')

@export(u'英式音标', 2)
def fld_phonetic_uk(self):
    return self._get_field('phonitic_uk')
```

### Decorating the Field (optional)

Using ```@with_style(**kwargs)``` to specify the css style strings or files, javascript strings or files, whether wrapping the css to avoid latent style interference.

```python
@with_styles(cssfile='_youdao.css', need_wrap_css=True, wrap_class='youdao')
def _get_singledict(self, single_dict, lang='eng'):
    url = "http://m.youdao.com/singledict?q=%s&dict=%s&le=%s&more=false" % (
        self.word, single_dict, lang)
    try:
        return urllib2.urlopen(url, timeout=5).read()
    except:
        return ''
```

## MdxService

This addon implement the local dictionary base service supporting mdx and stardict formats. By default, the service only extracts the entire explanation with the field name "default". It is impossible for this base service to extract all the intended fields for any given dictionary, but the user can create a inherited service for a path-specified dictionary.

**[Sample](samples/LDOCE6.py)**.

### Inherit `MdxService` class

```@register(label)``` is used to register the service, and parameter ```label``` as the dictionary name will be shown in the dictioary list.

```python
@register('Sample-LDOCE6')
class Ldoce6(MdxService):
    """service implementation"""
```

### Define Dictionary Field

```python
@export(u'音标', 1)
def fld_phonetic(self):
    html = self.get_html()
    m = re.search(r'<span class="pron">(.*?)</span>', html)
    if m:
        return m.groups()[0]
    return ''
```

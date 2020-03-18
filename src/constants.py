#-*- coding:utf-8 -*-
from .gui.lang import _, _sl

VERSION = '4.2.20180101'


class Endpoint:
    repository = u'https://github.com/finalion/WordQuery'
    feedback_issue = u'https://github.com/finalion/WordQuery/issues'
    feedback_mail = u'finalion@gmail.com'
    check_version = u'https://raw.githubusercontent.com/finalion/WordQuery/gh-pages/version'
    new_version = u'https://github.com/finalion/WordQuery'
    service_shop = u'https://finalion.github.io/WordQuery/shop.html'
    user_guide = u'https://finalion.github.io/WordQuery/'


class Template:
    tmpl_about = u'<b>{t0}</b><br />{version}<br /><b>{t1}</b><br /><a href="{url}">{url}</a><br /><b>{t2}</b><br /><a href="{feedback0}">{feedback0}</a><br /></a>'.format(
        t0=_('VERSION'), version=VERSION, t1=_('REPOSITORY'), url=Endpoint.repository,
        t2=_('FEEDBACK'), feedback0=Endpoint.feedback_issue)
    new_version = u'{info} <a href="{url}">V{version}</a>'.format(
        info=_('NEW_VERSION'), url=Endpoint.new_version, version='{version}')
    latest_version = _('LATEST_VERSION')
    abnormal_version = _('ABNORMAL_VERSION')
    check_failure = u'{msg}'
    miss_css = u'MDX dictonary <b>{dict}</b> misses css file <b>{css}</b>. <br />Please choose the file.'

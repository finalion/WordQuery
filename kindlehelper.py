#-*- coding:utf-8 -*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')  # helps with odd formatting
import sqlite3
import aqt
from aqt import mw
from aqt.qt import *


def import_kindle_vocab(path):
    conn = sqlite3.connect(path)
    c = conn.cursor()

    for row in c.execute('SELECT word,stem,lang,timestamp FROM words'):
        print row

    c.close()
    conn.close()


action = QAction(u"导入Kindle生词表", mw)
action.triggered.connect(import_kindle_vocab)
actionSep = QAction("", mw)
actionSep.setSeparator(True)
mw.form.menuCol.insertAction(mw.form.actionExit, actionSep)
mw.form.menuCol.insertAction(actionSep, action)


if __name__ == '__main__':
    file = sys.argv[1] if len(sys.argv) > 1 else 'dicts/vocab.db'

    import_kindle_vocab(file)

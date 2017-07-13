#-*- coding:utf-8 -*-
#
# Copyright © 2016–2017 Liang Feng <finalion@gmail.com>
#
# Support: Report an issue at https://github.com/finalion/WordQuery/issues
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version; http://www.gnu.org/copyleft/gpl.html.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import json
from collections import defaultdict

from aqt import mw
from aqt.qt import QCheckBox, QComboBox, QRadioButton
from aqt.utils import shortcut, showInfo, showText

from .lang import _
from .odds import get_model_byId, get_ord_from_fldname

VERSION = 'V4.1.20170714'
CONFIG_FILENAME = '.wqcfg.json'


class Config(object):

    def __init__(self, window):
        self.path = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), CONFIG_FILENAME)
        self.window = window
        self.version = '0'
        self.read()

    @property
    def pmname(self):
        return self.window.pm.name

    def update(self, data):
        data['version'] = VERSION
        data['%s_last' % self.pmname] = data.get('last_model', 0)
        self.data.update(data)
        with open(self.path, 'wb') as f:
            json.dump(self.data, f)

    def read(self):
        try:
            with open(self.path, 'rb') as f:
                self.data = json.load(f)
                # self.version = self.data.get('version', '0')
                # if VERSION != self.version:
                #     # showInfo(VERSION + self.version)
                #     self.last_model_id, self.dirs = 0, list()
        except:
            self.data = dict()

    def get_maps(self, model_id):
        return self.data.get(str(model_id), list())

    @property
    def last_model_id(self):
        return self.data.get('%s_last' % self.pmname, 0)

    @property
    def dirs(self):
        return self.data.get('dirs', list())

    @property
    def use_filename(self):
        return self.data.get('use_filename', True)

    @property
    def export_media(self):
        return self.data.get('export_media', False)


config = Config(mw)

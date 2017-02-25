#-*- coding:utf-8 -*-
import os
from collections import defaultdict
from aqt import mw
from aqt.qt import QCheckBox, QComboBox, QRadioButton
from .odds import get_model_byId, get_ord_from_fldname
import cPickle
from aqt.utils import shortcut, showInfo
from lang import _

VERSION = '20170225000'


class Config(object):

    def __init__(self, window):
        self.path = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), '.wqcfg')
        self.window = window
        self.data = dict()
        self.version = '0'
        self.read()

    @property
    def pmname(self):
        return self.window.pm.name

    def save_options_dialog(self, dialog):
        comboboxs, labels = dialog.findChildren(
            QComboBox), dialog.findChildren(QRadioButton)
        dict_cbs, field_cbs = comboboxs[::2], comboboxs[1::2]
        model = get_model_byId(self.window.col.models, self.last_model_id)
        maps = [{"word_checked": label.isChecked(), "dict": dict_cb.currentText().strip(),
                 "dict_path": dict_cb.itemData(dict_cb.currentIndex()) if dict_cb.itemData(dict_cb.currentIndex()) else "",
                 "dict_field": field_cb.currentText().strip(), "fld_ord": get_ord_from_fldname(model, label.text())}
                for (dict_cb, field_cb, label) in zip(dict_cbs, field_cbs, labels)]
        # profilename: {'last':last_model_id, '..model_id..':[..maps..]}
        self.data[self.last_model_id] = maps
        self.data['%s_last' % self.pmname] = self.last_model_id
        self.data['version'] = VERSION
        with open(self.path, 'wb') as f:
            cPickle.dump(self.data, f)
        # showInfo(str([label.text() for label in labels[3:]]))

    def save_mdxmanage_dialog(self, dialog):
        # {'dirs': []}
        # showInfo(str(dialog.dirs))
        self.data['dirs'] = dialog.dirs
        self.data['mdxs'] = dialog.dict_paths
        self.data['use_mdx_filename'] = dialog.chk_use_filename.isChecked()
        self.data['export_media'] = dialog.chk_export_media.isChecked()
        with open(self.path, 'wb') as f:
            cPickle.dump(self.data, f)

    def save_mdxs(self):
        # {'mdx': [(dict_path, dict_name), ]}
        pass

    def read(self):
        try:
            with open(self.path, 'rb') as f:
                self.data = cPickle.load(f)
                try:
                    self.last_model_id = self.data['%s_last' % self.pmname]
                    self.maps = self.data[self.last_model_id]
                    self.dirs = self.data.get('dirs', [])
                    self.version = self.data.get('version')
                    if VERSION != self.version:
                        showInfo(VERSION + self.version)

                        self.maps, self.last_model_id, self.dirs = list(),  0, list()
                except Exception as e:
                    showInfo(str(e))
                    self.maps, self.last_model_id, self.dirs = list(),  0, list()

        except:
            self.maps, self.last_model_id, self.dirs = list(),  0, list()
        # showInfo(str(self.maps))

    def get_maps(self, model_id):
        # showInfo(str(self.data[self.pmname]))
        return self.data.get(model_id, list())

    def get_dirs(self):
        return self.data.get('dirs', list())

    def get_mdxs(self):
        return self.data.get('mdxs', list())

    def use_mdx_filename(self):
        return self.data.get('use_mdx_filename', True)

    def export_media(self):
        return self.data.get('export_media', False)

maps = list()
# last_model_id  {pm_name:id}
last_model_id = -1000
# [model_id: maps]
mappings = defaultdict(list)

# action context: editor? browser?
context = defaultdict(int)

config = Config(mw)

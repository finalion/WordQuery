#-*- coding:utf-8 -*-
import os
from collections import defaultdict
from aqt.qt import QCheckBox, QComboBox, QLabel
from .odds import get_model_byId, get_ord_from_fldname
import cPickle
from aqt.utils import shortcut, showInfo


class Config(object):

    def __init__(self, window):
        self.path = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), '.wqcfg')
        self.window = window
        self.data = dict()

    @property
    def pmname(self):
        return self.window.pm.name

    def save(self, dialog):
        from .ui import OptionsDialog, MdxManageDialog
        if isinstance(dialog, OptionsDialog):
            self.save_options_dialog(dialog)
        if isinstance(dialog, MdxManageDialog):
            self.save_mdxmanage_dialog(dialog)

    def save_options_dialog(self, dialog):
        checkboxs, comboboxs, labels = dialog.findChildren(
            QCheckBox), dialog.findChildren(QComboBox), dialog.findChildren(QLabel)
        dict_cbs, field_cbs = comboboxs[::2], comboboxs[1::2]
        model = get_model_byId(self.window.col.models, self.last_model_id)
        maps = [{"checked": checkbox.isChecked(), "dict": dict_cb.currentText().strip(),
                 "dict_field": field_cb.currentText().strip(), "fld_ord": get_ord_from_fldname(model, label.text())}
                for (checkbox, dict_cb, field_cb, label) in zip(checkboxs, dict_cbs, field_cbs, labels)]
        # profilename: {'last':last_model_id, '..model_id..':[..maps..]}
        self.data[self.last_model_id] = maps
        self.data['%s_last' % self.pmname] = self.last_model_id
        with open(self.path, 'wb') as f:
            cPickle.dump(self.data, f)

    def save_mdxmanage_dialog(self, dialog):
        # {'dirs': []}
        # showInfo(str(dialog.dirs))
        self.data['dirs'] = dialog.dirs
        self.data['mdxs'] = dialog.dict_paths

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
                except:
                    self.maps, self.last_model_id, self.dirs = list(), 0, list()

        except:
            self.maps, self.last_model_id, self.dirs = list(), 0, list()

    def get_maps(self, model_id):
        # showInfo(str(self.data[self.pmname]))
        return self.data.get(model_id, list())

    def get_dirs(self):
        return self.data.get('dirs', list())

# anki import
import anki
import aqt
from aqt.studydeck import StudyDeck
from aqt.utils import shortcut, showInfo
from PyQt5 import Qt, QtCore, QtGui, QtWidgets
import os

from . import ui_options, ui_dicts_setting, ui_dict_chooser
from .lang import _, _sl
from ..service import service_manager
from ..context import config
from ..utils import MapDict, get_icon, get_model_byId, get_ord_from_fldname
from ..constants import VERSION, Endpoint, Template

class DictChooser(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = ui_dict_chooser.Ui_Form()
        self.ui.setupUi(self)
        self.ui.comboDicts.currentIndexChanged.connect(self.fill_comboFields)
        self.is_word = False

    def set_field_name(self, name):
        self.ui.btnCheckWord.setText(name)

    @property
    def btn_check(self):
        return self.ui.btnCheckWord

    @property
    def combo_dicts(self):
        return self.ui.comboDicts

    @property
    def combo_dict_fields(self):
        return self.ui.comboDictFields

    def status(self):
        service_id = self.ui.comboDicts.itemData(self.ui.comboDicts.currentIndex())
        return {
            "word_checked": self.ui.btnCheckWord.isChecked(),
            "dict": self.ui.comboDicts.currentText().strip(),
            "dict_unique": service_id if service_id else "",
            "dict_field": self.ui.comboDictFields.currentText().strip()
            }

    def update(self, data=None):
        """
        update combo contents
        """
        if data:
            note_field, word_checked, dict_name, dict_unique, dict_field = (
                data.get('fld_name', ''),
                data.get('word_checked', False),
                data.get('dict', _('NOT_DICT_FIELD')),
                data.get('dict_unique', ''),
                data.get('dict_field', ''),)
            self.ui.btnCheckWord.setChecked(word_checked)
            self.ui.btnCheckWord.setText(note_field)
        else:
            dict_name = self.ui.comboDicts.currentText()
            dict_field = self.ui.comboDicts.currentText()
        # fill comboDicts
        self.fill_comboDicts()
        self.ui.comboDicts.setCurrentText(dict_name)
        self.ui.comboDictFields.setCurrentText(dict_field)

    def fill_comboDicts(self):
        self.ui.comboDicts.clear()
        # add "not dict field"
        self.ui.comboDicts.addItem(_('NOT_DICT_FIELD'))
        self.ui.comboDicts.insertSeparator(self.ui.comboDicts.count())
        # add local services
        for service in service_manager.local_services:
            # combo_data.insert("data", each.label)
            self.ui.comboDicts.addItem(
                service.title, userData=service.unique)
        # add web services
        self.ui.comboDicts.insertSeparator(self.ui.comboDicts.count())
        for service in service_manager.web_services:
            self.ui.comboDicts.addItem(
                service.title, userData=service.unique)

    def fill_comboFields(self, combo_dict_index):
        self.is_word = (combo_dict_index == 0)
        # showInfo("select dict index: "+str(combo_dict_index))
        self.ui.comboDictFields.clear()
        if not self.is_word:
            self.ui.comboDictFields.setEnabled(True)
            # showInfo("select dict service: "+str(service_unique))
            current_service = service_manager.get_service(
                self.ui.comboDicts.itemData(combo_dict_index)
                )
            if not current_service:
                return
            for each in current_service.fields:
                self.ui.comboDictFields.addItem(each)
        else:
            self.ui.comboDictFields.setEnabled(False)

class OptionsDlg(QtWidgets.QDialog):

    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = ui_options.Ui_Dialog()
        self.ui.setupUi(self)
        self.btn_group = QtWidgets.QButtonGroup()
        # init from saved data
        self.current_model = None
        if not config.last_model_id:
            return
        self.current_model = get_model_byId(aqt.mw.col.models, config.last_model_id)
        if self.current_model:
            self.ui.btnModelChooser.setText(
                u'%s [%s]' % (_('CHOOSE_NOTE_TYPES'),  self.current_model['name']))
            # build fields -- dicts layout
            self.build_mappings_layout(self.current_model)

    def build_mappings_layout(self, note_model):
        self.ui.lwDicts.clear()
        maps = config.get_maps(note_model['id'])
        # self.radio_group = QButtonGroup()
        for i, fld in enumerate(note_model['flds']):
            ord, name = fld['ord'], fld['name']
            if maps:
                for j, each in enumerate(maps):
                    if each.get('fld_ord', -1) == ord:
                        self.add_dict_widget(fld_name = name, **each)
                        break
                else:
                    self.add_dict_widget(fld_name = name)
            else:
                self.add_dict_widget(fld_name = name)

    def add_dict_widget(self, **data):
        widget = DictChooser()
        widget.update(data)
        self.btn_group.addButton(widget.btn_check)
        item = QtWidgets.QListWidgetItem()
        item.setSizeHint(widget.sizeHint()) #important
        self.ui.lwDicts.insertItem(self.ui.lwDicts.count(), item)
        self.ui.lwDicts.setItemWidget(item, widget)

        # self.ui.lwDicts.setMaximumHeight(widget.height()*self.ui.lwDicts.count())
        # showInfo(str(widget.height())+","+str(self.ui.lwDicts.height()))
        return widget

    def show_dictSetting_dlg(self):
        """ show dict setting dialog
        """
        dict_dlg = DictSettingDlg(self)
        dict_dlg.activateWindow()
        dict_dlg.raise_()
        if dict_dlg.exec_() == QtWidgets.QDialog.Accepted:
            # update local services
            service_manager.update_services()
            for chooser in self.ui.lwDicts.findChildren(DictChooser):
                chooser.update()

    def show_models(self):
        """show model selection dialog which is created by anki.
        """
        edit = QtWidgets.QPushButton(anki.lang._("Manage"),
                           clicked=lambda: aqt.models.Models(aqt.mw, self))
        ret = StudyDeck(aqt.mw, names=lambda: sorted(aqt.mw.col.models.allNames()),
                        accept=anki.lang._("Choose"), title=anki.lang._("Choose Note Type"),
                        help="_notes", parent=self, buttons=[edit],
                        cancel=True, geomKey="selectModel")
        if not ret.name:
            return
        model = aqt.mw.col.models.byName(ret.name)
        self.ui.btnModelChooser.setText(
            u'%s [%s]' % (_('CHOOSE_NOTE_TYPES'), ret.name))
        if model:
            self.build_mappings_layout(model)
        self.current_model = model

    def show_about(self):
        """show About dialog
        """
        QtWidgets.QMessageBox.about(self, _('ABOUT'), Template.tmpl_about)

    def save(self):
        self.close()
        if not self.current_model:
            return
        data = dict()
        maps = []
        for chooser in self.ui.lwDicts.findChildren(DictChooser):
            status = chooser.status()
            status['fld_ord'] = get_ord_from_fldname(self.current_model, chooser.btn_check.text())
            maps.append(status)
        current_model_id = self.current_model['id']
        data[current_model_id] = maps
        data['last_model'] = current_model_id
        config.update(data)

class DictSettingDlg(QtWidgets.QDialog):
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)
        self.ui = ui_dicts_setting.Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.listWidgetFolders.addItems(config.dirs)
        self.ui.checkUseFilename.setChecked(config.use_filename)
        self.ui.checkExportMedia.setChecked(config.export_media)
        self.accepted.connect(self.save)
        self._dict_paths = []
        self._dirs = []

    def add_folder(self):
        dir_ = QtWidgets.QFileDialog.getExistingDirectory(
            self, caption=u"Select Folder", directory="", 
            options=QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks)
        if dir_:
            self.ui.listWidgetFolders.addItem(dir_)

    def remove_folder(self):
        item = self.ui.listWidgetFolders.takeItem(self.ui.listWidgetFolders.currentRow())
        del item

    def find_mdxes(self):
        for each in self.dirs:
            for dirpath, dirnames, filenames in os.walk(each):
                self._dict_paths.extend([os.path.join(dirpath, filename)
                                         for filename in filenames if filename.lower().endswith(u'.mdx')])
        self._dict_paths = list(set(self._dict_paths))
        return self._dict_paths

    def save(self):
        #save data
        data = {'dirs': self.dirs,
                'use_filename': self.ui.checkUseFilename.isChecked(),
                'export_media': self.ui.checkExportMedia.isChecked()}
        config.update(data)
        
    @property
    def dict_paths(self):
        return self.find_mdxes()

    @property
    def dirs(self):
        return [self.ui.listWidgetFolders.item(i).text()
                for i in range(self.ui.listWidgetFolders.count())]
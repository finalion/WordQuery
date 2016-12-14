#-*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import os
import anki
import aqt
from aqt import mw
from aqt.qt import *
import aqt.models
from aqt.studydeck import StudyDeck
from aqt.utils import shortcut, showInfo
# import trackback
import cPickle
import wquery
# import wquery.context as c
from service import service_manager
from mdict.mdict_query import IndexBuilder
from .config import Config
from .odds import get_model_byId, get_ord_from_fldname
from utils import MapDict

c = Config(mw)


class MdxManageDialog(QDialog):

    def __init__(self, parent=0):
        QDialog.__init__(self, parent)
        self.parent = parent
        self._dict_paths = []
        self.build()
        self.activateWindow()
        self.raise_()

    def build(self):
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("+")
        remove_btn = QPushButton("-")
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        add_btn.clicked.connect(self.add_folder)
        remove_btn.clicked.connect(self.remove_folder)
        self.folders_lst = QListWidget()
        self.folders_lst.addItems(c.get_dirs())
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        layout.addLayout(btn_layout)
        layout.addWidget(self.folders_lst)
        layout.addWidget(ok_btn)
        self.setLayout(layout)
        self.activateWindow()
        self.raise_()

    def add_folder(self):
        dir_ = QFileDialog.getExistingDirectory(self,
                                                caption="Select Folder", directory="", options=QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if dir_:
            self.folders_lst.addItem(dir_)

    def remove_folder(self):
        item = self.folders_lst.takeItem(self.folders_lst.currentRow())
        del item

    def find_mdxes(self):
        dirs = self.dirs
        for each in dirs:
            for dirpath, dirnames, filenames in os.walk(each):
                self._dict_paths.extend([os.path.join(dirpath, filename)
                                         for filename in filenames if filename.endswith('.mdx')])
        return list(set(self._dict_paths))

    @property
    def dict_paths(self):
        return self.find_mdxes()

    @property
    def dirs(self):
        return [self.folders_lst.item(i).text()
                for i in range(self.folders_lst.count())]


def index_mdx(paths):
    mw.progress.start(immediate=True, label="Index building...")
    index_thread = MdxIndexer(paths)
    index_thread.start()
    while not index_thread.isFinished():
        mw.app.processEvents()
        index_thread.wait(100)
    mw.progress.finish()
    return index_thread.index_builders


class MdxIndexer(QThread):

    def __init__(self, paths):
        QThread.__init__(self)
        self.paths = paths
        self.index_builders = list()

    def run(self):
        for path in self.paths:
            ib = IndexBuilder(path)
            self.index_builders.append(
                MapDict(builder=ib, title=ib._title if ib._title else os.path.basename(path), path=path))


def show_options():
    c.read()
    mw.options_dialog = dialog = OptionsDialog(mw)


class OptionsDialog(QDialog):

    def __init__(self, parent=0):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle(u"Options")
        self.signal_mapper_chk = QSignalMapper(self)
        # self.accepted.connect(self.parent.update_dicts_list)
        self.build()
        self.show()
        self.activateWindow()
        self.raise_()

    def build(self):
        self.mdxs = index_mdx(c.data.get('mdxs', []))
        self.main_layout = QVBoxLayout()
        models_layout = QHBoxLayout()
        scroll_area = QScrollArea()
        dicts_widget = QWidget()
        self.dicts_layout = QVBoxLayout(scroll_area)
        dicts_widget.setLayout(self.dicts_layout)
        scroll_area.setWidget(dicts_widget)
        scroll_area.setWidgetResizable(True)
        mdx_button = QPushButton(u"mdx文件夹")
        mdx_button.clicked.connect(self.show_mdx_dialog)
        self.models_button = QPushButton(u"选择笔记类型")
        self.models_button.clicked.connect(self.btn_models_pressed)
        models_layout.addWidget(mdx_button)
        models_layout.addWidget(self.models_button)
        if c.last_model_id:
            model = get_model_byId(mw.col.models, c.last_model_id)
            if model:
                self.models_button.setText(
                    u'选择笔记类型 [当前类型 -- %s]' % model['name'])
                # build fields -- dicts layout
                self.build_layout(model)
        ok_button = QPushButton(u"OK")
        ok_button.clicked.connect(self.btn_ok_pressed)
        self.main_layout.addLayout(models_layout)
        self.main_layout.addWidget(scroll_area)
        # main_layout.addLayout(dicts_layout)
        self.main_layout.addWidget(ok_button)
        self.signal_mapper_chk.mapped.connect(self.chkbox_state_changed)
        self.setLayout(self.main_layout)

    def show_mdx_dialog(self):
        mdx_dialog = MdxManageDialog(self)
        if mdx_dialog.exec_() == QDialog.Accepted:
            dict_paths = mdx_dialog.dict_paths
            # showInfo(str(dict_paths))
            index_builders = index_mdx(dict_paths)
            c.save(mdx_dialog)
            self.update_dicts_list(index_builders)

    def btn_ok_pressed(self):
        self.close()
        c.save(self)
        # index_mdx(-1)

    def btn_models_pressed(self):
        model = self.show_models()
        if model:
            self.build_layout(model)

    def chkbox_state_changed(self, fld_number):
        dict_checks = self.findChildren(QCheckBox)
        combos = self.findChildren(QComboBox)
        dict_combos, field_combos = combos[::2], combos[1::2]
        dict_combos[fld_number].setEnabled(
            dict_checks[fld_number].checkState() != 0)
        field_combos[fld_number].setEnabled(
            dict_checks[fld_number].checkState() != 0)

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clear_layout(item.layout())

    def build_layout(self, model):
        self.clear_layout(self.dicts_layout)
        maps = c.get_maps(model['id'])
        for i, fld in enumerate(model['flds']):
            ord = fld['ord']
            name = fld['name']
            if maps:
                for j, each in enumerate(maps):
                    if each.get('fld_ord', -1) == ord:
                        self.add_dict_layout(j, fld_name=name, checked=each[
                            'checked'], dict=each['dict'], dict_field=each['dict_field'])
                        break
                else:
                    self.add_dict_layout(j, fld_name=name)
            else:
                self.add_dict_layout(i, fld_name=name)
        self.setLayout(self.main_layout)

    def show_models(self):
        c.save(self)
        edit = QPushButton(
            _("Manage"), clicked=lambda: aqt.models.Models(mw, self))
        ret = StudyDeck(
            mw, names=lambda: sorted(mw.col.models.allNames()), accept=_("Choose"), title=_("Choose Note Type"),
            help="_notes", parent=self, buttons=[edit],
            cancel=True, geomKey="selectModel")
        if ret.name:
            model = mw.col.models.byName(ret.name)
            c.last_model_id = model['id']
            self.models_button.setText(u'选择笔记类型 [当前类型 -- %s]' % ret.name)
            return model

    def dict_combobox_activated(self, index):
        combos = self.findChildren(QComboBox)
        dict_combos, field_combos = combos[::2], combos[1::2]
        assert len(dict_combos) == len(field_combos)
        for i, dict_combo in enumerate(dict_combos):
            # in windows and linux: the combo has current focus,
            # in mac: the combo's listview has current focus, and the listview can
            # be got by view()
            if dict_combo.hasFocus() or dict_combo.view().hasFocus():
                dict_combo_text = dict_combo.currentText()
                if dict_combo_text == u'本地Mdx词典':
                    field_combos[i].clear()
                    path = QFileDialog.getOpenFileName(
                        caption="select dictionary", directory="", filter="mdx Files(*.mdx)")
                    if path:
                        field_combos[i].setEditText(path.decode('utf-8'))
                    else:
                        field_combos[i].setEditText("")
                        # field_combos[i].setFocus(1)  # MouseFocusReason
                elif dict_combo_text == u'Mdx服务器':
                    field_combos[i].clear()
                    field_combos[i].setEditText('http://')
                    field_combos[i].setFocus(1)  # MouseFocusReason
                else:
                    field_text = field_combos[i].currentText()
                    field_combos[i].clear()
                    current_service = service_manager.get_service(
                        dict_combo.currentText())
                    if current_service and current_service.instance.fields:
                        for each in current_service.instance.fields:
                            field_combos[i].addItem(each)
                            if each == field_text:
                                field_combos[i].setEditText(field_text)
                break

    def add_dict_layout(self, i, **kwargs):
        """
        kwargs:
        checked  dict  fld_name dict_field
        """
        checked, dict_name, fld_name, dict_field = kwargs.get('checked', False), kwargs.get(
            'dict', ''), kwargs.get('fld_name', ''),  kwargs.get('dict_field', '')
        layout = QGridLayout()
        dict_check = QCheckBox(u"使用字典")
        if i == 0:
            checked, dict_name = False, ""
            dict_check.setEnabled(False)
        dict_check.setChecked(checked)
        dict_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        fldname_label = QLabel(fld_name)
        fldname_label.setMinimumSize(80, 0)
        fldname_label.setMaximumSize(80, 30)
        fldname_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        dict_combo = QComboBox()
        dict_combo.setMinimumSize(140, 0)
        dict_combo.setEnabled(checked)
        # dict_combo.setEditable(True)
        dict_combo.setFocusPolicy(0x1 | 0x2 | 0x8 | 0x4)
        dict_combo.addItems([each['title'] for each in self.mdxs])
        dict_combo.insertSeparator(dict_combo.count())
        dict_combo.addItems([s.label for s in service_manager.services])
        dict_name = dict_name if service_manager.get_service(dict_name) else ""
        dict_combo.setEditText(dict_name)
        dict_combo.activated.connect(self.dict_combobox_activated)

        field_combo = QComboBox()
        field_combo.setMinimumSize(100, 0)
        field_combo.setMaximumSize(100, 30)
        field_combo.setEnabled(checked)
        service = service_manager.get_service(dict_name)
        if service and service.instance.fields:
            field_combo.addItems(service.instance.fields)
        field_combo.setEditable(True)
        dict_field = dict_field if dict_name else ""
        field_combo.setEditText(dict_field)
        # field_combo.setEditable(False)
        # field_combo.activated.connect(combobox_activated)

        self.connect(dict_check, SIGNAL("clicked()"),
                     self.signal_mapper_chk, SLOT("map()"))
        self.signal_mapper_chk.setMapping(dict_check, i)
        layout.addWidget(dict_check, i, 0)
        layout.addWidget(fldname_label, i, 1)
        layout.addWidget(dict_combo, i, 2)
        layout.addWidget(field_combo, i, 3)
        # layout.addWidget(choose_btn, i, 3)
        self.dicts_layout.addLayout(layout)
        self.setLayout(self.main_layout)
        # for osx
        # mw.options_dialog.activateWindow()
        # mw.options_dialog.raise_()

    def update_dicts_list(self, builders):
        # mdx_data: path, title
        comboboxs = self.findChildren(QComboBox)
        dict_cbs, field_cbs = comboboxs[::2], comboboxs[1::2]
        mdx_items = [builder.title for builder in builders]
        web_items = [s.label for s in service_manager.services]
        for cb in dict_cbs:
            cb.clear()
            cb.addItems(mdx_items)
            cb.insertSeparator(cb.count())
            cb.addItems(web_items)

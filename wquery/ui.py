#-*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import anki
import aqt
from aqt import mw
from aqt.qt import *
from aqt.studydeck import StudyDeck
from aqt.utils import shortcut, showInfo, showText, tooltip, getFile
# import trackback
import cPickle
import wquery
import wquery.context as c
from service import service_manager


def _get_model_byId(id):
    for m in list(mw.col.models.all()):
        # showInfo(str(m['id']) + ', ' + m['name'])
        if m['id'] == id:
            return m


def _get_ord_from_fldname(model, name):
    flds = model['flds']
    for fld in flds:
        if fld['name'] == name:
            return fld['ord']


def set_parameters():
    checkboxs, comboboxs, labels = mw.myWidget.findChildren(
        QCheckBox), mw.myWidget.findChildren(QComboBox), mw.myWidget.findChildren(QLabel)
    dict_cbs, field_cbs = comboboxs[::2], comboboxs[1::2]
    model = _get_model_byId(c.last_model_id)
    c.maps = [{"checked": checkbox.isChecked(), "dict": dict_cb.currentText().strip(),
               "dict_field": field_cb.currentText().strip(), "fld_ord": _get_ord_from_fldname(model, label.text())}
              for (checkbox, dict_cb, field_cb, label) in zip(checkboxs, dict_cbs, field_cbs, labels)]
    # update mappings
    c.mappings[c.last_model_id] = c.maps
    # save the last model set to read next time
    c.mappings['last'] = c.last_model_id
    with open(c.cfgpath, 'wb') as f:
        cPickle.dump(c.mappings, f)


def btn_ok_pressed():
    mw.myWidget.close()
    set_parameters()
    # index_mdx(-1)


def btn_models_pressed():
    model = show_models()
    if model:
        build_layout(model)


def chkbox_state_changed(fld_number):
    dict_checks = mw.myWidget.findChildren(QCheckBox)
    combos = mw.myWidget.findChildren(QComboBox)
    dict_combos, field_combos = combos[::2], combos[1::2]
    dict_combos[fld_number].setEnabled(
        dict_checks[fld_number].checkState() != 0)
    field_combos[fld_number].setEnabled(
        dict_checks[fld_number].checkState() != 0)

combo_index = 0
def combo_clicked(fld_number):
    global combo_index
    combo_index = fld_number
    showInfo(str(fld_number))
    
def clear_layout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clear_layout(item.layout())

# model has 6 properties.
# name, mod, flds, tmpls, tags, id


def build_layout(model):
    clear_layout(mw.myDictsLayout)
    c.maps = c.mappings[model['id']]
    for i, fld in enumerate(model['flds']):
        ord = fld['ord']
        name = fld['name']
        if c.maps:
            for j, each in enumerate(c.maps):
                if each.get('fld_ord', -1) == ord:
                    add_dict_layout(j, fld_name=name, checked=each[
                                    'checked'], dict=each['dict'], dict_field=each['dict_field'])
                    break
            else:
                add_dict_layout(j, fld_name=name)
        else:
            add_dict_layout(i, fld_name=name)
    mw.myWidget.setLayout(mw.myMainLayout)


def show_models():
    set_parameters()
    ret = StudyDeck(
        mw, names=lambda: sorted(mw.col.models.allNames()), accept=_("Choose"), title=_("Choose Note Type"),
        help="_notes", parent=mw.myWidget,
        cancel=True, geomKey="selectModel")
    if ret.name:
        model = mw.col.models.byName(ret.name)
        c.last_model_id = model['id']
        mw.myChooseButton.setText(u'选择笔记类型 [当前类型 -- %s]' % ret.name)
        return model


def dict_combobox_activated(index):
    combos = mw.myWidget.findChildren(QComboBox)
    dict_combos, field_combos = combos[::2], combos[1::2]
    assert len(dict_combos) == len(field_combos)
    for i, dict_combo in enumerate(dict_combos):
        if dict_combo.hasFocus():  # useless on mac
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
def dict_combobox_activated2(index):
    combos = mw.myWidget.findChildren(QComboBox)
    dict_combos, field_combos = combos[::2], combos[1::2]
    assert len(dict_combos) == len(field_combos)
    # showInfo(str(combo_index))
    dict_combo, field_combo = dict_combos[combo_index], field_combos[combo_index]
    
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

def add_dict_layout(i, **kwargs):
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
    fldname_label.setMinimumSize(100, 0)
    fldname_label.setMaximumSize(100, 100)
    fldname_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    dict_combo = QComboBox()
    dict_combo.setMinimumSize(100, 0)
    dict_combo.setEnabled(checked)
    dict_combo.setEditable(True)
    dict_combo.setFocusPolicy(0x1 | 0x2 | 0x8 | 0x4)
    dict_combo.addItems([s.label for s in service_manager.services])

    dict_name = dict_name if service_manager.get_service(dict_name) else ""
    dict_combo.setEditText(dict_name)
    dict_combo.activated.connect(dict_combobox_activated)

    field_combo = QComboBox()
    field_combo.setMinimumSize(120, 0)
    field_combo.setEnabled(checked)
    service = service_manager.get_service(dict_name)
    if service and service.instance.fields:
        field_combo.addItems(service.instance.fields)
    field_combo.setEditable(True)
    dict_field = dict_field if dict_name else ""
    field_combo.setEditText(dict_field)
    # field_combo.setEditable(False)
    # field_combo.activated.connect(combobox_activated)

    mw.myWidget.connect(dict_check, SIGNAL("clicked()"),
                        mw.signal_mapper_chk, SLOT("map()"))
    mw.myWidget.connect(dict_combo, SIGNAL("currentIndexChanged()"),
                        mw.signal_mapper_combo, SLOT("map()"))
    mw.signal_mapper_chk.setMapping(dict_check, i)
    mw.signal_mapper_combo.setMapping(dict_combo, i)
    layout.addWidget(dict_check, i, 0)
    layout.addWidget(fldname_label, i, 1)
    layout.addWidget(dict_combo, i, 2)
    layout.addWidget(field_combo, i, 3)
    # layout.addWidget(choose_btn, i, 3)
    mw.myDictsLayout.addLayout(layout)
    mw.myWidget.setLayout(mw.myMainLayout)


def show_options():
    wquery.read_parameters()
    mw.myWidget = widget = QWidget()
    mw.myMainLayout = main_layout = QVBoxLayout()
    models_layout = QHBoxLayout()
    mw.myScrollArea = scroll_area = QScrollArea()
    mw.myDictsWidget = dicts_widget = QWidget()
    mw.myDictsLayout = dicts_layout = QVBoxLayout(scroll_area)
    dicts_widget.setLayout(dicts_layout)
    scroll_area.setWidget(dicts_widget)
    scroll_area.setWidgetResizable(True)
    mw.signal_mapper_chk = QSignalMapper(mw.myWidget)
    mw.signal_mapper_combo = QSignalMapper(mw.myWidget)
    # mw.myModelNameLabel = QLabel(u"笔记类型")
    mw.myChooseButton = models_button = QPushButton(u"选择笔记类型")
    models_button.clicked.connect(btn_models_pressed)
    models_layout.addWidget(models_button)
    if c.last_model_id:
        model = _get_model_byId(c.last_model_id)
        if model:
            models_button.setText(u'选择笔记类型 [当前类型 -- %s]' % model['name'])
            # build fields -- dicts layout
            build_layout(model)
    ok_button = QPushButton(u"OK")
    ok_button.clicked.connect(btn_ok_pressed)
    main_layout.addLayout(models_layout)
    main_layout.addWidget(scroll_area)
    # main_layout.addLayout(dicts_layout)
    main_layout.addWidget(ok_button)
    mw.signal_mapper_chk.mapped.connect(chkbox_state_changed)
    mw.signal_mapper_combo.mapped.connect(combo_clicked)
    widget.setLayout(main_layout)
    widget.show()

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
from wquery.query import index_mdx
import wquery.context as c
from anki.hooks import addHook, runHook, wrap


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
    cbs, les, lbs = mw.myWidget.findChildren(
        QCheckBox), mw.myWidget.findChildren(QComboBox), mw.myWidget.findChildren(QLabel)
    model = _get_model_byId(c.model_id)
    c.maps = [{"checked": cb.isChecked(), "dict_path": le.currentText().strip(),
               "fld_ord": _get_ord_from_fldname(model, lb.text()), "youdao": c.lang}
              for (cb, le, lb) in zip(cbs, les, lbs)]
    # update mappings
    c.mappings[c.model_id] = c.maps
    # save the last model set to read next time
    c.mappings['last'] = c.model_id
    with open(c.cfgpath, 'wb') as f:
        cPickle.dump(c.mappings, f)


def btn_ok_pressed():
    mw.myWidget.close()
    set_parameters()
    index_mdx(-1)


def btn_models_pressed():
    model = show_models()
    if model:
        build_layout(model)


def chkbox_state_changed(fld_number):
    dict_checks = mw.myWidget.findChildren(QCheckBox)
    dict_combos = mw.myWidget.findChildren(QComboBox)
    dict_combos[fld_number].setEnabled(
        dict_checks[fld_number].checkState() != 0)


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


def build_layout(model=None):
    # wquery.read_parameters()
    clear_layout(mw.myDictsLayout)
    if not model:
        model = _get_model_byId(c.model_id)
    c.maps = c.mappings[model['id']]
    for i, fld in enumerate(model['flds']):
        ord = fld['ord']
        name = fld['name']
        if c.maps:
            for j, each in enumerate(c.maps):
                if each.get('fld_ord', -1) == ord:
                    add_dict_layout(j, fld_name=name, checked=each[
                                    'checked'], dict_path=each['dict_path'])
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
        c.model_id = model['id']
        mw.myChooseButton.setText(u'选择笔记类型 [当前类型 -- %s]' % ret.name)
        return model

app = QApplication.instance()


def combobox_activated(index):
    dict_combos = mw.myWidget.findChildren(QComboBox)
    for combo in dict_combos:
        if combo.hasFocus():
            if index == 0:
                path = QFileDialog.getOpenFileName(
                    caption="select dictionary", directory="", filter="mdx Files(*.mdx)")
                if path:
                    path = path.decode('utf-8')
                    combo.lineEdit().setText(path)
                else:
                    combo.lineEdit().setText("")
            if index == 1:
                combo.lineEdit().setText('http://')
            break


def add_dict_layout(i, **kwargs):
    """
    kwargs:
    checked  dict_path  fld_name
    """
    checked, dict_path, fld_name, lang = kwargs.get('checked', False), kwargs.get(
        'dict_path', ''), kwargs.get('fld_name', ''), kwargs.get('youdao', 'eng')
    layout = QGridLayout()
    dict_check = QCheckBox(u"使用字典")
    if i == 0:
        checked, dict_path = False, ""
        dict_check.setEnabled(False)
    dict_check.setChecked(checked)
    dict_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    dict_combo = QComboBox()
    dict_combo.setMinimumSize(180, 0)
    dict_combo.setEnabled(checked)
    dict_combo.setEditable(True)
    dict_combo.setFocusPolicy(0x1 | 0x2 | 0x8 | 0x4)
    dict_combo.addItems([u'选择mdx词典...', u'设定mdx服务器...'])
    dict_combo.insertSeparator(2)
    dict_combo.addItems(c.available_youdao_fields[lang].keys())
    dict_combo.setEditText(dict_path)
    dict_combo.activated.connect(combobox_activated)
    # path_edit = QLineEdit(dict_path)
    # path_edit.setReadOnly(not checked)
    # objname = "fld%d" % i
    # path_edit.setObjectName(objname)
    # important! only myWidget can find the children!!!!
    # when use some joined string, it can not find too !!!
    # ss = mw.myWidget.findChildren(QLineEdit, objname)
    # if ss:
    #     showInfo("found %d" % i)
    field_label = QLabel(fld_name)
    field_label.setMinimumSize(100, 0)
    field_label.setMaximumSize(100, 100)
    field_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    mw.myWidget.connect(dict_check, SIGNAL("clicked()"),
                        mw.signal_mapper_chk, SLOT("map()"))
    mw.signal_mapper_chk.setMapping(dict_check, i)
    layout.addWidget(dict_check, i, 0)
    layout.addWidget(field_label, i, 1)
    layout.addWidget(dict_combo, i, 2)
    # layout.addWidget(choose_btn, i, 3)
    mw.myDictsLayout.addLayout(layout)
    mw.myWidget.setLayout(mw.myMainLayout)


def _update_dicts_combo(lang):
    cbs = mw.myWidget.findChildren(QComboBox)
    for i, box in enumerate(cbs):
        box.clear()
        box.addItems([u'选择mdx词典...', u'设定mdx服务器...'])
        box.insertSeparator(2)
        box.addItems(c.available_youdao_fields[lang].keys())
        # showInfo('%d, %s' % (i, str(c.maps)))
        if c.maps and c.maps[i].get('lang', 'eng') == lang:
            box.setEditText(c.maps[i].get('dict_path', ''))
        else:
            box.setEditText('')


def youdao_eng_clicked(checked):
    if checked:
        c.lang = 'eng'
        _update_dicts_combo('eng')


def youdao_fr_clicked(checked):
    if checked:
        c.lang = 'fr'
        _update_dicts_combo('fr')


def youdao_jap_clicked(checked):
    if checked:
        c.lang = 'jap'
        _update_dicts_combo('jap')


def youdao_ko_clicked(checked):
    if checked:
        c.lang = 'ko'
        _update_dicts_combo('ko')


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
    # mw.myModelNameLabel = QLabel(u"笔记类型")
    mw.myChooseButton = models_button = QPushButton(u"选择笔记类型")
    models_button.clicked.connect(btn_models_pressed)
    models_layout.addWidget(models_button)
    if c.model_id:
        model = _get_model_byId(c.model_id)
        if model:
            models_button.setText(u'选择笔记类型 [当前类型 -- %s]' % model['name'])
            # build fields -- dicts layout
            if c.maps:
                build_layout()
    mw.myYoudaoCheck = youdao_check_group = QGroupBox(u"有道词典")
    youdao_layout = QHBoxLayout()
    eng_check, fr_check, jap_check, ko_check = QRadioButton(
        u"中英"), QRadioButton(u"中法"), QRadioButton(u"中日"), QRadioButton(u"中韩")
    youdao_layout.addWidget(eng_check)
    youdao_layout.addWidget(fr_check)
    youdao_layout.addWidget(jap_check)
    youdao_layout.addWidget(ko_check)
    youdao_type_maps = {'eng': eng_check, 'fr': fr_check,
                        'jap': jap_check, 'ko': ko_check}
    if c.maps:
        lang = c.maps[0].get('youdao', 'eng')
    else:
        lang = 'eng'
    youdao_type_maps[lang].setChecked(True)
    eng_check.clicked.connect(youdao_eng_clicked)
    fr_check.clicked.connect(youdao_fr_clicked)
    jap_check.clicked.connect(youdao_jap_clicked)
    ko_check.clicked.connect(youdao_ko_clicked)
    youdao_check_group.setLayout(youdao_layout)
    ok_button = QPushButton(u"OK")
    ok_button.clicked.connect(btn_ok_pressed)
    main_layout.addLayout(models_layout)
    main_layout.addWidget(youdao_check_group)
    main_layout.addWidget(scroll_area)
    # main_layout.addLayout(dicts_layout)
    main_layout.addWidget(ok_button)
    mw.signal_mapper_chk.mapped.connect(chkbox_state_changed)
    widget.setLayout(main_layout)
    widget.show()

#-*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import anki
import aqt
from aqt import mw
from aqt.qt import *
from aqt.studydeck import StudyDeck
from aqt.utils import shortcut, showInfo, showText, tooltip
# import trackback
import cPickle
import wquery
from wquery.query import index_mdx
import wquery.context as c
from anki.hooks import addHook, runHook, wrap


def _get_model_byId(id):
    for m in list(mw.col.models.all()):
        if m['id'] == id:
            return m


def set_parameters():
    cbs, les, lbs = mw.myWidget.findChildren(
        QCheckBox), mw.myWidget.findChildren(QLineEdit), mw.myWidget.findChildren(QLabel)
    c.maps = [{"checked": cb.isChecked(), "dict_path": le.text().strip(), "fld_name": lb.text()}
              for (cb, le, lb) in zip(cbs, les, lbs)]
    # update mappings
    c.mappings[c.model_id] = c.maps
    # save the last model set to read next time
    c.mappings['last'] = c.model_id
    with open(c.savepath, 'wb') as f:
        cPickle.dump(c.mappings, f)
        # cPickle.dump({'maps': c.maps,
        #               'model': c.model_id}, f)


def btn_ok_pressed():
    mw.myWidget.close()
    set_parameters()
    index_mdx(-1)


def btn_models_pressed():
    model = show_models()
    if model:
        build_layout(model)


def select_dict(fld_number):
    path = QFileDialog.getOpenFileName(
        caption="select dictionary", directory="", filter="mdx Files(*.mdx)")
    if path:
        path = path.decode('utf-8')
        path_edits = mw.myWidget.findChildren(QLineEdit)
        path_edits[fld_number].setText(path)


def chkbox_state_changed(fld_number):
    dict_checks = mw.myWidget.findChildren(QCheckBox)
    line_edits = mw.myWidget.findChildren(QLineEdit)
    line_edits[fld_number].setReadOnly(
        dict_checks[fld_number].checkState() == 0)


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
    if model:
        c.maps = c.mappings[c.model_id]
        if c.mappings[c.model_id]:
            for i, each in enumerate(c.maps):
                add_dict_layout(i, **each)
        else:
            for i, fld in enumerate(model['flds']):
                add_dict_layout(i, fld_name=fld['name'])
    else:
        # build from config
        for i, each in enumerate(c.maps):
            add_dict_layout(i, **each)
    mw.myWidget.setLayout(mw.myMainLayout)


def mode_changed():
    c.mode_id = mw.col.decks.current()['mid']
    c.maps = c.mappings[c.model_id]

addHook('currentModelChanged', mode_changed)


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


def add_dict_layout(i, **kwargs):
    """
    kwargs:
    checked  dict_path  fld_name
    """
    checked, dict_path, fld_name = kwargs.get('checked', False), kwargs.get(
        'dict_path', ''), kwargs.get('fld_name', '')
    layout = QHBoxLayout()
    dict_check = QCheckBox(u"使用字典")
    choose_btn = QPushButton(u"选择")
    if i == 0:
        checked, dict_path = False, ""
        dict_check.setEnabled(False)
        choose_btn.setEnabled(False)
    dict_check.setChecked(checked)
    path_edit = QLineEdit(dict_path)
    path_edit.setReadOnly(not checked)
    objname = "fld%d" % i
    path_edit.setObjectName(objname)
    # important! only myWidget can find the children!!!!
    # when use some joined string, it can not find too !!!
    # ss = mw.myWidget.findChildren(QLineEdit, objname)
    # if ss:
    #     showInfo("found %d" % i)
    field_label = QLabel(fld_name)
    mw.myWidget.connect(choose_btn, SIGNAL("clicked()"),
                        mw.signal_mapper_sel, SLOT("map()"))
    mw.myWidget.connect(dict_check, SIGNAL("clicked()"),
                        mw.signal_mapper_chk, SLOT("map()"))
    mw.signal_mapper_sel.setMapping(choose_btn, i)
    mw.signal_mapper_chk.setMapping(dict_check, i)
    layout.addWidget(dict_check)
    layout.addWidget(field_label)
    layout.addWidget(path_edit)
    layout.addWidget(choose_btn)
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
    mw.signal_mapper_sel = QSignalMapper(mw.myWidget)
    mw.signal_mapper_chk = QSignalMapper(mw.myWidget)
    # mw.myModelNameLabel = QLabel(u"笔记类型")
    mw.myChooseButton = models_button = QPushButton(u"选择笔记类型")
    models_button.clicked.connect(btn_models_pressed)
    if c.model_id:
        model_name = _get_model_byId(c.model_id)['name']
        models_button.setText(u'选择笔记类型 [当前类型 -- %s]' % model_name)
    models_layout.addWidget(models_button)
    # build fields -- dicts layout
    if c.maps:
        build_layout()
    ok_button = QPushButton(u"OK")
    ok_button.clicked.connect(btn_ok_pressed)
    main_layout.addLayout(models_layout)
    main_layout.addWidget(scroll_area)
    # main_layout.addLayout(dicts_layout)
    main_layout.addWidget(ok_button)
    mw.signal_mapper_sel.mapped.connect(select_dict)
    mw.signal_mapper_chk.mapped.connect(chkbox_state_changed)
    widget.setLayout(main_layout)
    widget.show()

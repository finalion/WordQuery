#-*- coding:utf-8 -*-


def get_model_byId(models, id):
    for m in list(models.all()):
        # showInfo(str(m['id']) + ', ' + m['name'])
        if m['id'] == id:
            return m


def get_ord_from_fldname(model, name):
    flds = model['flds']
    for fld in flds:
        if fld['name'] == name:
            return fld['ord']

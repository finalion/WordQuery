# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\Users\finalion\AppData\Roaming\Anki2\addons21\wordquery\gui\dict_chooser.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(341, 34)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout.setContentsMargins(6, 5, 6, 5)
        self.horizontalLayout.setSpacing(18)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnCheckWord = QtWidgets.QRadioButton(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnCheckWord.sizePolicy().hasHeightForWidth())
        self.btnCheckWord.setSizePolicy(sizePolicy)
        self.btnCheckWord.setMinimumSize(QtCore.QSize(100, 0))
        self.btnCheckWord.setMaximumSize(QtCore.QSize(100, 16777215))
        self.btnCheckWord.setObjectName("btnCheckWord")
        self.horizontalLayout.addWidget(self.btnCheckWord)
        self.comboDicts = QtWidgets.QComboBox(Form)
        self.comboDicts.setObjectName("comboDicts")
        self.horizontalLayout.addWidget(self.comboDicts)
        self.comboDictFields = QtWidgets.QComboBox(Form)
        self.comboDictFields.setObjectName("comboDictFields")
        self.horizontalLayout.addWidget(self.comboDictFields)
        self.horizontalLayout.setStretch(1, 1)
        self.horizontalLayout.setStretch(2, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.btnCheckWord.setText(_translate("Form", "Word field"))


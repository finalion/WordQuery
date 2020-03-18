# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\Users\finalion\AppData\Roaming\Anki2\addons21\wordquery\gui\options.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(525, 412)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.btnDictChooser = QtWidgets.QPushButton(Dialog)
        self.btnDictChooser.setObjectName("btnDictChooser")
        self.horizontalLayout_2.addWidget(self.btnDictChooser)
        self.btnModelChooser = QtWidgets.QPushButton(Dialog)
        self.btnModelChooser.setObjectName("btnModelChooser")
        self.horizontalLayout_2.addWidget(self.btnModelChooser)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.lwDicts = QtWidgets.QListWidget(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lwDicts.sizePolicy().hasHeightForWidth())
        self.lwDicts.setSizePolicy(sizePolicy)
        self.lwDicts.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.lwDicts.setObjectName("lwDicts")
        self.verticalLayout.addWidget(self.lwDicts)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnParameter = QtWidgets.QPushButton(Dialog)
        self.btnParameter.setObjectName("btnParameter")
        self.horizontalLayout.addWidget(self.btnParameter)
        self.btnUpdate = QtWidgets.QPushButton(Dialog)
        self.btnUpdate.setObjectName("btnUpdate")
        self.horizontalLayout.addWidget(self.btnUpdate)
        self.btnAbout = QtWidgets.QPushButton(Dialog)
        self.btnAbout.setObjectName("btnAbout")
        self.horizontalLayout.addWidget(self.btnAbout)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(Dialog)
        self.lwDicts.setCurrentRow(-1)
        self.btnDictChooser.clicked.connect(Dialog.show_dictSetting_dlg)
        self.btnModelChooser.clicked.connect(Dialog.show_models)
        self.buttonBox.accepted.connect(Dialog.save)
        self.btnAbout.clicked.connect(Dialog.show_about)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Options"))
        self.btnDictChooser.setText(_translate("Dialog", "Dict folders"))
        self.btnModelChooser.setText(_translate("Dialog", "Choose note types"))
        self.btnParameter.setText(_translate("Dialog", "Settings"))
        self.btnUpdate.setText(_translate("Dialog", "Update"))
        self.btnAbout.setText(_translate("Dialog", "About"))


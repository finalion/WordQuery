# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\Users\finalion\AppData\Roaming\Anki2\addons21\wordquery\gui\dicts_setting.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(348, 300)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.btnAddFolder = QtWidgets.QPushButton(Dialog)
        self.btnAddFolder.setObjectName("btnAddFolder")
        self.horizontalLayout.addWidget(self.btnAddFolder)
        self.btnRemoveFolder = QtWidgets.QPushButton(Dialog)
        self.btnRemoveFolder.setObjectName("btnRemoveFolder")
        self.horizontalLayout.addWidget(self.btnRemoveFolder)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.listWidgetFolders = QtWidgets.QListWidget(Dialog)
        self.listWidgetFolders.setObjectName("listWidgetFolders")
        self.verticalLayout.addWidget(self.listWidgetFolders)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.checkUseFilename = QtWidgets.QCheckBox(Dialog)
        self.checkUseFilename.setObjectName("checkUseFilename")
        self.horizontalLayout_2.addWidget(self.checkUseFilename)
        self.checkExportMedia = QtWidgets.QCheckBox(Dialog)
        self.checkExportMedia.setObjectName("checkExportMedia")
        self.horizontalLayout_2.addWidget(self.checkExportMedia)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        self.btnAddFolder.clicked.connect(Dialog.add_folder)
        self.btnRemoveFolder.clicked.connect(Dialog.remove_folder)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dicts Setting"))
        self.btnAddFolder.setText(_translate("Dialog", "Add Folder"))
        self.btnRemoveFolder.setText(_translate("Dialog", "Remove Folder"))
        self.checkUseFilename.setText(_translate("Dialog", "Use filename as dict label"))
        self.checkExportMedia.setText(_translate("Dialog", "Export media files"))


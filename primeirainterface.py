# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\Mario Venere Neto\Desktop\testeqt.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(491, 182)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.lineEditinserir = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEditinserir.setGeometry(QtCore.QRect(60, 20, 113, 20))
        self.lineEditinserir.setObjectName("lineEditinserir")
        self.lineEditcolar = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEditcolar.setGeometry(QtCore.QRect(60, 80, 113, 20))
        self.lineEditcolar.setObjectName("lineEditcolar")
        self.pushButtoncopiar = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtoncopiar.setGeometry(QtCore.QRect(220, 20, 75, 23))
        self.pushButtoncopiar.setObjectName("pushButtoncopiar")
        self.pushButtoncolar = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtoncolar.setGeometry(QtCore.QRect(220, 80, 75, 23))
        self.pushButtoncolar.setObjectName("pushButtoncolar")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 491, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.pushButtoncopiar.pressed.connect(self.lineEditinserir.selectAll) # type: ignore
        self.pushButtoncopiar.released.connect(self.lineEditinserir.copy) # type: ignore
        self.pushButtoncolar.clicked.connect(self.lineEditcolar.paste) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Primeira Interface"))
        self.pushButtoncopiar.setText(_translate("MainWindow", "Copiar"))
        self.pushButtoncolar.setText(_translate("MainWindow", "Colar"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

import sys
from datetime import datetime,timedelta
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import *
from cowin import COWIN
import pandas as pd

class CalWidget(QLineEdit):
    def __init__(self, parent=None):
        super(CalWidget, self).__init__(parent)
        self.calButton = QToolButton(self)
        self.calButton.setIcon(QtGui.QIcon('calendar_icon.png'))
        self.calButton.setStyleSheet('border: 0px; padding: 0px;')
        self.calButton.setCursor(QtCore.Qt.ArrowCursor)
        self.calButton.clicked.connect(self.showCalWid)

    def resizeEvent(self, event):
        buttonSize = self.calButton.sizeHint()
        frameWidth = self.style().pixelMetric(QCommonStyle.PM_DefaultFrameWidth)
        self.calButton.move(self.rect().right() - frameWidth - buttonSize.width(),
                            (self.rect().bottom() - buttonSize.height() + 1))#/2)
        super(CalWidget, self).resizeEvent(event)

    def showCalWid(self):
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumDate(QtCore.QDate(datetime.today().date()-timedelta(days=60)))
        self.calendar.setMaximumDate(QtCore.QDate(datetime.today().date()+timedelta(days=7)))
        self.calendar.setVerticalHeaderFormat(False)
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.updateDate)
        self.calendar.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.calendar.setStyleSheet('background: white; color: black')
        self.calendar.setGridVisible(True)
        pos = QtGui.QCursor.pos()
        self.calendar.setGeometry(pos.x(), pos.y(),300, 200)
        self.calendar.show()

    def updateDate(self,*args):
        getDate = self.calendar.selectedDate().toString('dd-MM-yyyy')
        self.setText(getDate)
        self.calendar.deleteLater()

class MainDialog(QMainWindow,COWIN):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.centralwidget = QWidget(self)

        self.layout = QVBoxLayout(self.centralwidget)

        self.calButton = CalWidget()

        self.layout.addWidget(self.calButton)
        self.buttonBox = QDialogButtonBox(self.centralwidget)
        self.buttonBox.setGeometry(QtCore.QRect(50, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("ButtonBox")
        self.buttonBox.rejected.connect(self.exit_event)
        self.buttonBox.accepted.connect(self.accepted_event)

        self.layout.addWidget(self.buttonBox)

        self.setCentralWidget(self.centralwidget)

    def accepted_event(self):
        print('calButton.text = ',self.calButton.text())

        if not self.calButton.text():
            self.msg = QMessageBox()
            self.msg.setIcon(QMessageBox.Warning)
            self.msg.setText("User clicked 'OK' button without selecting Dates")
            self.msg.setInformativeText("Generating Session data on the basis of date {0}".format((datetime.today().date()+timedelta(days=1)).strftime('%d-%m-%Y')))
            self.msg.setWindowTitle("MessageBox")
            self.msg.setDefaultButton(QMessageBox.Ignore)
            self.msg.setEscapeButton(QMessageBox.Abort)
            self.msg.setStandardButtons(QMessageBox.Ignore | QMessageBox.Abort)
            self.msg.buttonClicked.connect(self.popup_button)
            self.msg.show()
        else:
            self.retrieve_session_data()

    def retrieve_session_data(self):

        user_date = self.calButton.text() if self.calButton.text() else (datetime.today().date()+timedelta(days=1)).strftime('%d-%m-%Y')
        #df = pd.read_csv(r'C:\Users\khushal\PycharmProjects\netwrok_tutorial\find_session_by_district.csv')
        df = self.extract_data_from_api(input_date=user_date,user_pincode=None)

        if isinstance(df,pd.DataFrame):

            df.reset_index(drop=True,inplace=True)

            header = list(df.columns)
            rows_len = len(df)
            columns_len = len(header)

            self.tbl = QTableWidget()
            self.tbl.setRowCount(rows_len)
            self.tbl.setColumnCount(columns_len)
            self.tbl.setHorizontalHeaderLabels(header)

            for inx in df.index:
                #print(df.iloc[inx])
                self.tbl.insertRow(inx)
                for x in range(columns_len):
                    self.tbl.setItem(inx,x,QTableWidgetItem(str(df.iloc[inx][x])))

        #Table will fit the screen horizontally
            self.tbl.horizontalHeader().setStretchLastSection(True)
            self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tbl.show()

        else:

            self.msg1 = QMessageBox()
            self.msg1.setIcon(QMessageBox.Warning)
            self.msg1.setText("For {0},No Sessions available right now for Current User location".format(user_date))
            self.msg1.setInformativeText('Current User Location is City- {0}, District- {1}, State- {2}'.format(self.current_user_location['city'],\
                                                self.current_user_location['district'],self.current_user_location['state']))

            self.msg1.setWindowTitle("Error-Message")
            self.msg1.setDefaultButton(QMessageBox.Ignore)
            self.msg1.setEscapeButton(QMessageBox.Abort)
            self.msg1.setStandardButtons(QMessageBox.Close)
            self.msg1.buttonClicked.connect(self.popup_button)
            self.msg1.show()

    def popup_button(self,i):
        print('popup_button = ',i.text())
        if i.text() == 'Ignore':
            self.retrieve_session_data()
        else:
            self.exit_event()

    def exit_event(self):
        print('Cancel Button pressed,Closing the current session')
        self.close()

def main():
    app = QApplication(sys.argv)
    form = MainDialog()
    form.resize(200,200)
    form.setWindowTitle("Cowin")
    form.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
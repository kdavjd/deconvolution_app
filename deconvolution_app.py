import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QComboBox, QGridLayout
from PyQt5.QtCore import QSize
import pandas as pd
import chardet
import os
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class CSVViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.df = pd.DataFrame()
        self.initUI()

    def initUI(self):
        self.setMinimumSize(QSize(960, 720))  # Задаем минимальный размер окна

        # Инициализируем layout в виде таблицы
        self.layout = QGridLayout()

        self.button = QPushButton('Load CSV', self)
        self.button.clicked.connect(self.getCSV)

        self.comboBoxX = QComboBox()
        self.comboBoxY = QComboBox()

        self.buttonPlot = QPushButton('Plot', self)
        self.buttonPlot.clicked.connect(self.plotGraph)

        self.buttonInteractive = QPushButton('Interactive Mode', self)
        self.buttonInteractive.setCheckable(True)
        self.buttonInteractive.clicked.connect(self.interactiveMode)

        self.table = QTableWidget()
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        # Добавляем виджеты в таблицу
        self.layout.addWidget(self.button, 0, 0)
        self.layout.addWidget(self.comboBoxX, 0, 1)
        self.layout.addWidget(self.comboBoxY, 0, 2)
        self.layout.addWidget(self.buttonPlot, 1, 0)
        self.layout.addWidget(self.buttonInteractive, 1, 1)
        self.layout.addWidget(self.table, 2, 0, 1, 3)
        self.layout.addWidget(self.canvas, 3, 0, 1, 3)

        self.setLayout(self.layout)


    def getCSV(self):
        self.fileName, _ = QFileDialog.getOpenFileName(self, 'Open CSV', os.getenv('HOME'), 'CSV(*.csv)')
        if self.fileName:
            self.loadCSV()

    def loadCSV(self):
        # Определение кодировки файла
        with open(self.fileName, 'rb') as f:
            result = chardet.detect(f.read())
        file_encoding = result['encoding']

        # Считывание данных из CSV файла
        self.df = pd.read_csv(
            self.fileName,
            encoding=file_encoding,
        )

        self.fillComboBoxes(self.df)

        # Отображение DataFrame в виджете QTableWidget
        self.fillTable(self.df)

    def fillTable(self, data):
        self.table.setRowCount(data.shape[0])
        self.table.setColumnCount(data.shape[1])
        self.table.setHorizontalHeaderLabels(data.columns)
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                self.table.setItem(i, j, QTableWidgetItem(str(data.iat[i, j])))

    def fillComboBoxes(self, data):
        self.comboBoxX.clear()
        self.comboBoxY.clear()
        self.comboBoxX.addItems(data.columns)
        self.comboBoxY.addItems(data.columns)

    def plotGraph(self):
        x = self.df[self.comboBoxX.currentText()]
        y = self.df[self.comboBoxY.currentText()]

        # Очищаем текущий график
        self.figure.clear()

        # Создаем новый график
        ax = self.figure.add_subplot(111)

        # Отрисовываем график
        ax.plot(x, y, '*-')

        # Обновляем область отображения графика
        self.canvas.draw()

    def interactiveMode(self, activated):
        if activated:
            self.cid = self.canvas.mpl_connect('button_press_event', self.onclick)
        else:
            self.canvas.mpl_disconnect(self.cid)

    def onclick(self, event):
        ax = self.figure.get_axes()[0]
        ax.plot(event.xdata, event.ydata, 'ro')
        self.canvas.draw()

def main():
    app = QApplication(sys.argv)
    viewer = CSVViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

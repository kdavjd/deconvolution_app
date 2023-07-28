import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QComboBox, QGridLayout, QLabel, QStackedWidget
from PyQt5.QtCore import QSize
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from csv_viewer import CSVViewer
import numpy as np
from scipy.stats import norm


class MainApp(QWidget): # Класс наследуется от QWidget и является основным классом приложения.
    def __init__(self):
        super().__init__()

        self.viewer = CSVViewer() # Создаем экземпляр класса CSVViewer, который будет заниматься обработкой CSV файлов.

        self.initUI()

    def initUI(self):
        self.setMinimumSize(QSize(960, 720))  # Задаем минимальный размер окна

        self.buttonLoadCSV = QPushButton('Load CSV', self)
        self.buttonLoadCSV.clicked.connect(self.getCSV)

        self.labelX = QLabel('Select X:', self)
        self.comboBoxX = QComboBox()

        self.labelY = QLabel('Select Y:', self)
        self.comboBoxY = QComboBox()

        self.buttonPlot = QPushButton('Plot', self)
        self.buttonPlot.clicked.connect(self.plotGraph)

        self.buttonInteractive = QPushButton('Interactive Mode', self)
        self.buttonInteractive.setCheckable(True)
        self.buttonInteractive.clicked.connect(self.interactiveMode)

        self.buttonAddDiff = QPushButton('Add Diff', self)
        self.buttonAddDiff.clicked.connect(self.addDiff)

        self.csv_table = QTableWidget()
        self.gaussian_table = QTableWidget()
        self.gaussian_table.setColumnCount(4)
        self.gaussian_table.setHorizontalHeaderLabels(['Reaction', 'Height', 'Center', 'Width'])

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.csv_table)
        self.stacked_widget.addWidget(self.gaussian_table)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        self.buttonDeleteColumn = QPushButton('Delete X column', self)
        self.buttonDeleteColumn.clicked.connect(self.deleteColumn)

        self.layout = QGridLayout()

        self.layout.addWidget(self.buttonLoadCSV, 0, 0)
        self.layout.addWidget(self.buttonPlot, 1, 0)
        self.layout.addWidget(self.buttonInteractive, 2, 0)
        self.layout.addWidget(self.labelX, 0, 2)
        self.layout.addWidget(self.comboBoxX, 0, 3)
        self.layout.addWidget(self.labelY, 1, 2)
        self.layout.addWidget(self.comboBoxY, 1, 3)
        self.layout.addWidget(self.buttonAddDiff, 2, 2)
        self.layout.addWidget(self.buttonDeleteColumn, 2, 3)
        self.layout.addWidget(self.stacked_widget, 0, 4, 4, 1)
        self.layout.addWidget(self.canvas, 4, 0, 1, 5)

        self.setLayout(self.layout)

    def getCSV(self):
        self.viewer.getCSV()
        self.fillComboBoxes()
        self.fillTable()

    def fillTable(self):
        data = self.viewer.df
        self.csv_table.setRowCount(data.shape[0])
        self.csv_table.setColumnCount(data.shape[1])
        self.csv_table.setHorizontalHeaderLabels(data.columns)
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                self.csv_table.setItem(i, j, QTableWidgetItem(str(data.iat[i, j])))


    def fillComboBoxes(self):
        # Эта функция заполняет выпадающие меню выбора столбцов для отрисовки графика.
        # Функция использует загруженные данные (DataFrame) из класса CSVViewer.
        self.comboBoxX.clear()
        self.comboBoxY.clear()
        self.comboBoxX.addItems(self.viewer.df.columns)
        self.comboBoxY.addItems(self.viewer.df.columns)

    def interactiveMode(self, activated):
        # Эта функция переключает приложение в интерактивный режим,
        # где пользователь может рисовать гауссианы по графику.
        if activated:
            self.stacked_widget.setCurrentIndex(1)  # Индекс Гауссианной таблицы
            self.press_cid = self.canvas.mpl_connect('button_press_event', self.on_press)
            self.release_cid = self.canvas.mpl_connect('button_release_event', self.on_release)
        else:
            self.stacked_widget.setCurrentIndex(0)  # Индекс таблицы CSV
            self.canvas.mpl_disconnect(self.press_cid)
            self.canvas.mpl_disconnect(self.release_cid)

    def add_gaussian_to_table(self, height, center, width):
        row_count = self.gaussian_table.rowCount()
        self.gaussian_table.insertRow(row_count)
        self.gaussian_table.setItem(row_count, 0, QTableWidgetItem(f'Reaction_{row_count + 1}'))
        self.gaussian_table.setItem(row_count, 1, QTableWidgetItem(str(height)))
        self.gaussian_table.setItem(row_count, 2, QTableWidgetItem(str(center)))
        self.gaussian_table.setItem(row_count, 3, QTableWidgetItem(str(width)))

    def on_press(self, event):
        # Эта функция вызывается при нажатии кнопки мыши на графике в интерактивном режиме.
        self.press_x = event.xdata
        self.press_y = event.ydata
    
    def get_column_data(self, column_name):
        return self.viewer.df[column_name]

    def on_release(self, event):
        # Эта функция вызывается при отпускании кнопки мыши на графике в интерактивном режиме.
        release_x = event.xdata
        width = 2 * abs(release_x - self.press_x)  # Удвоенная ширина Гауссианы
        x_column_data = self.get_column_data(self.comboBoxX.currentText())
        x = np.linspace(min(x_column_data), max(x_column_data), 1000)  # Диапазон значений x
        y = self.gaussian(x, self.press_y, self.press_x, width)  # Значения Гауссианы

        ax = self.figure.get_axes()[0]
        ax.plot(x, y, 'r-')
        self.canvas.draw()
        
        self.add_gaussian_to_table(self.press_y, self.press_x, width)

    def gaussian(self, x, a0, a1, a2):
        return a0 * np.exp(((-1/2) * ((x - a1)/a2)**2))
          
    def addDiff(self):
        x_col_name = self.comboBoxX.currentText()
        y_col_name = self.comboBoxY.currentText()
        self.viewer.add_diff_column(x_col_name, y_col_name)
        self.fillTable()
        self.fillComboBoxes()
    
    def deleteColumn(self):
        # Эта функция удаляет выбранный столбец из DataFrame.
        col_name = self.comboBoxX.currentText()
        if col_name in self.viewer.df.columns:
            self.viewer.df = self.viewer.df.drop(columns=[col_name])
            self.fillTable()
            self.fillComboBoxes()
    
    def onclick(self, event):
        # Эта функция вызывается при клике на график в интерактивном режиме.        
        ax = self.figure.get_axes()[0]
        ax.plot(event.xdata, event.ydata, 'ro')
        self.canvas.draw()

    def plotGraph(self):
        # Эта функция отрисовывает график на основе выбранных пользователем данных из ComboBox.
        self.viewer.plotGraph(self.comboBoxX.currentText(), self.comboBoxY.currentText(), self.figure, self.canvas)

def main():
    app = QApplication(sys.argv)
    main_app = MainApp()
    main_app.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

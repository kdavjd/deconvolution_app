import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QTableView, QComboBox, QGridLayout, QLabel, QStackedWidget
from PyQt5.QtCore import QSize
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from csv_viewer import CSVViewer
from pandas_model import PandasModel
import numpy as np
import pandas as pd

class MainApp(QWidget): 
    def __init__(self):
        super().__init__()

        self.viewer = CSVViewer()

        self.initUI()

    def initUI(self):
        self.setMinimumSize(QSize(960, 720))  

        self.gaussian_data = pd.DataFrame(columns=['Reaction', 'Height', 'Center', 'Width'])
        self.gaussian_model = PandasModel(self.gaussian_data)
        self.gaussian_table = QTableView()
        self.gaussian_table.setModel(self.gaussian_model)

        self.csv_table = QTableView()

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.csv_table)
        self.stacked_widget.addWidget(self.gaussian_table)

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

        self.figure = Figure()
        self.figure.set_size_inches(10, 5, forward=True)
        self.canvas = FigureCanvas(self.figure)

        self.buttonDeleteColumn = QPushButton('Delete X column', self)
        self.buttonDeleteColumn.clicked.connect(self.deleteColumn)

        # Создаем главный вертикальный лейаут
        main_layout = QVBoxLayout()
        
        # Создаем горизонтальный лейаут для верхней области
        top_layout = QHBoxLayout()

        # Добавляем кнопки, лейблы и выпадающие списки в верхнюю область
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.buttonLoadCSV)
        buttons_layout.addWidget(self.buttonPlot)
        buttons_layout.addWidget(self.buttonInteractive)
        buttons_layout.addWidget(self.labelX)
        buttons_layout.addWidget(self.comboBoxX)
        buttons_layout.addWidget(self.labelY)
        buttons_layout.addWidget(self.comboBoxY)
        buttons_layout.addWidget(self.buttonAddDiff)
        buttons_layout.addWidget(self.buttonDeleteColumn)

        # Добавляем лейаут кнопок в верхний лейаут
        top_layout.addLayout(buttons_layout)

        # Добавляем таблицу в верхний лейаут
        top_layout.addWidget(self.stacked_widget)

        # Добавляем верхний лейаут в главный лейаут
        main_layout.addLayout(top_layout)

        # Добавляем холст для графика в главный лейаут
        main_layout.addWidget(self.canvas)

        self.setLayout(main_layout)


    def getCSV(self):
        self.viewer.getCSV()
        self.fillComboBoxes()
        self.fillTable()

    def fillTable(self):
        self.csv_model = PandasModel(self.viewer.df)
        self.csv_table.setModel(self.csv_model)

    def fillComboBoxes(self):
        self.comboBoxX.clear()
        self.comboBoxY.clear()
        self.comboBoxX.addItems(self.viewer.df.columns)
        self.comboBoxY.addItems(self.viewer.df.columns)

    def interactiveMode(self, activated):
        if activated:
            self.stacked_widget.setCurrentIndex(1)
            self.press_cid = self.canvas.mpl_connect('button_press_event', self.on_press)
            self.release_cid = self.canvas.mpl_connect('button_release_event', self.on_release)
        else:
            self.stacked_widget.setCurrentIndex(0)
            self.canvas.mpl_disconnect(self.press_cid)
            self.canvas.mpl_disconnect(self.release_cid)

    def add_gaussian_to_table(self, height, center, width):
        row_data = pd.DataFrame({'Reaction': [f'Reaction_{self.gaussian_data.shape[0] + 1}'], 
                                'Height': [height], 'Center': [center], 'Width': [width]})
        self.gaussian_data = pd.concat([self.gaussian_data, row_data], ignore_index=True)
        
        # обновляем модель таблицы
        self.gaussian_model = PandasModel(self.gaussian_data)
        self.gaussian_table.setModel(self.gaussian_model)

    def on_press(self, event):
        self.press_x = event.xdata
        self.press_y = event.ydata

    def get_column_data(self, column_name):
        return self.viewer.df[column_name]

    def on_release(self, event):
        release_x = event.xdata
        width = 2 * abs(release_x - self.press_x)
        x_column_data = self.get_column_data(self.comboBoxX.currentText())
        x = np.linspace(min(x_column_data), max(x_column_data), 1000)
        y = self.gaussian(x, self.press_y, self.press_x, width)

        ax = self.figure.get_axes()[0]
        ax.plot(x, y, 'r-')
        self.canvas.draw()
        
        self.add_gaussian_to_table(self.press_y, self.press_x, width)

    def gaussian(self, x, a0, a1, a2):
                return a0 * np.exp(-((x - a1) ** 2) / (2 * a2 ** 2))

    def plotGraph(self):
        self.figure.clear()
        
        ax = self.figure.add_subplot(111)
        ax.plot(self.viewer.df[self.comboBoxX.currentText()], self.viewer.df[self.comboBoxY.currentText()], 'b-')
        
        self.canvas.draw()

    def addDiff(self):
        x_column = self.comboBoxX.currentText()
        y_column = self.comboBoxY.currentText()
        self.viewer.add_diff_column(x_column, y_column)
        self.fillTable()
        self.fillComboBoxes()

    def deleteColumn(self):
        if self.stacked_widget.currentIndex() == 0:
            self.viewer.df.drop([self.comboBoxX.currentText()], axis=1, inplace=True)
            self.fillTable()
            self.fillComboBoxes()
        elif self.stacked_widget.currentIndex() == 1:
            if self.gaussian_table.currentIndex().row() >= 0:
                self.gaussian_data.drop(self.gaussian_table.currentIndex().row(), inplace=True)
                self.gaussian_data.reset_index(drop=True, inplace=True)
                self.gaussian_model = PandasModel(self.gaussian_data)
                self.gaussian_table.setModel(self.gaussian_model)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainApp()
    ex.show()
    sys.exit(app.exec_())

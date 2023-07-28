import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QTableView, QComboBox, QGridLayout, QLabel, QStackedWidget
from PyQt5.QtCore import QSize
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from csv_viewer import CSVViewer
from pandas_model import PandasModel
from table_manager import TableManager
import numpy as np
import pandas as pd

class MainApp(QWidget): 
    """Главное приложение."""
    
    def __init__(self):
        """Инициализация класса."""
        super().__init__()

        self.viewer = CSVViewer()
        self.tableManager = TableManager(self.viewer)

        self.initUI()

    def initUI(self):
        """Инициализация пользовательского интерфейса."""
        self.setMinimumSize(QSize(960, 720))  

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

        main_layout = QVBoxLayout()
        
        top_layout = QHBoxLayout()

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

        top_layout.addLayout(buttons_layout)

        top_layout.addWidget(self.tableManager.stacked_widget)

        main_layout.addLayout(top_layout)

        main_layout.addWidget(self.canvas)

        self.setLayout(main_layout)


    def getCSV(self):
        """Получение данных из CSV."""
        self.viewer.getCSV()
        self.tableManager.fillComboBoxes(self.comboBoxX, self.comboBoxY)
        self.tableManager.fillTable()

    def interactiveMode(self, activated):
        """Интерактивный режим."""
        if activated:
            self.tableManager.stacked_widget.setCurrentIndex(1)
            self.press_cid = self.canvas.mpl_connect('button_press_event', self.on_press)
            self.release_cid = self.canvas.mpl_connect('button_release_event', self.on_release)
        else:
            self.tableManager.stacked_widget.setCurrentIndex(0)
            self.canvas.mpl_disconnect(self.press_cid)
            self.canvas.mpl_disconnect(self.release_cid)

    def on_press(self, event):
        """Событие при нажатии кнопки мыши."""
        self.press_x = event.xdata
        self.press_y = event.ydata

    def get_column_data(self, column_name):
        column_data = self.viewer.df[column_name]
        # Проверьте, являются ли данные числовыми
        if pd.to_numeric(column_data, errors='coerce').notna().all():
            return column_data
        else:
            raise ValueError(f"Column {column_name} contains non-numeric data")

    def on_release(self, event):
        """Событие при отпускании кнопки мыши."""
        release_x = event.xdata
        width = 2 * abs(release_x - self.press_x)
        x_column_data = self.get_column_data(self.comboBoxX.currentText())
        x = np.linspace(min(x_column_data), max(x_column_data), 1000)
        y = self.gaussian(x, self.press_y, self.press_x, width)

        ax = self.figure.get_axes()[0]
        ax.plot(x, y, 'r-')
        self.canvas.draw()
        
        self.tableManager.add_gaussian_to_table(self.press_y, self.press_x, width)

    def gaussian(self, x, a0, a1, a2):
        """Гауссовская функция."""
        return a0 * np.exp(-((x - a1) ** 2) / (2 * a2 ** 2))

    def plotGraph(self):
        """Построение графика."""
        self.figure.clear()
        
        ax = self.figure.add_subplot(111)
        ax.plot(self.viewer.df[self.comboBoxX.currentText()], self.viewer.df[self.comboBoxY.currentText()], 'b-')
        
        self.canvas.draw()

    def addDiff(self):
        """Добавление дифференцирования."""
        x_column = self.comboBoxX.currentText()
        y_column = self.comboBoxY.currentText()
        self.viewer.add_diff_column(x_column, y_column)
        self.tableManager.fillTable()
        self.tableManager.fillComboBoxes(self.comboBoxX, self.comboBoxY)

    def deleteColumn(self):
        """Удаление колонки."""
        self.tableManager.deleteColumn(self.comboBoxX, self.comboBoxY, self.tableManager.stacked_widget.currentIndex())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainApp()
    ex.show()
    sys.exit(app.exec_())

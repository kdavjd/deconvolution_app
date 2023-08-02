import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt
from csv_viewer import CSVViewer
from pandas_model import PandasModel
from table_manager import TableManager
import numpy as np
import pandas as pd
from math_operations import MathOperations
from ui import UIInitializer 
from event_handler import EventHandler

# Импортируем matplotlib и применяем стиль
import matplotlib.pyplot as plt
import scienceplots
plt.style.use(['science', 'no-latex', 'notebook', 'grid'])


class MainApp(QWidget): 
    """Главное приложение."""
    
    def __init__(self):
        """Инициализация класса."""
        super().__init__()

        # Создаем экземпляры без аргументов
        self.viewer = CSVViewer()
        self.math_operations = MathOperations()
        
        # Создаем другие объекты, передавая в них ссылку на viewer
        self.tableManager = TableManager(self.viewer, self.math_operations)
        self.uiInitializer = UIInitializer(self, self.viewer)

        # Инициализируем CSVViewer, передав в него ссылки на tableManager и uiInitializer
        self.viewer.initialize(self.tableManager, self.uiInitializer)
        
        self.eventHandler = EventHandler(self)

        self.tableManager.gaussian_model.dataChangedSignal.connect(self.rebuildGaussians)
        self.eventHandler.connectSignals() 

    def switchToInteractiveMode(self, activated):
        """Переключение на интерактивный режим."""
        if activated:
            self.eventHandler.connectCanvasEvents()
        else:
            self.eventHandler.disconnectCanvasEvents()
          
    def rebuildGaussians(self):
        """Перестроение всех гауссиан по данным в таблице."""
        self.plotGraph()  # очистим график        
        ax = self.uiInitializer.figure.get_axes()[0]
        for _, row in self.tableManager.gaussian_data.iterrows():
            x_column_data = self.tableManager.get_column_data(self.uiInitializer.comboBoxX.currentText())
            x = np.linspace(min(x_column_data), max(x_column_data), 1000)
            if row['Type'] == 'gauss':
                y = self.math_operations.gaussian(x, row['Height'], row['Center'], row['Width'])
            else:
                y = self.math_operations.fraser_suzuki(x, row['Height'], row['Center'], row['Width'], -1)
            ax.plot(x, y, 'r-')

        self.uiInitializer.canvas.draw()

    def computePeaks(self):
        x_column = self.uiInitializer.comboBoxX.currentText()
        y_column = self.uiInitializer.comboBoxY.currentText()
        self.tableManager.computePeaks(x_column, y_column)
        self.rebuildGaussians()
    
    def plotGraph(self):
        """Построение графика."""
        x_column = self.uiInitializer.comboBoxX.currentText()
        y_column = self.uiInitializer.comboBoxY.currentText()

        if not x_column or not y_column:  # Если одно из значений пустое, прекратить функцию
            return

        self.uiInitializer.figure.clear()
        
        ax = self.uiInitializer.figure.add_subplot(111)
        ax.plot(self.viewer.df[x_column], self.viewer.df[y_column], 'b-')
        
        self.uiInitializer.canvas.draw()

    def addDiff(self):
        x_column = self.uiInitializer.comboBoxX.currentText()
        y_column = self.uiInitializer.comboBoxY.currentText()
        self.tableManager.addDiff(x_column, y_column, self.uiInitializer.comboBoxX, self.uiInitializer.comboBoxY)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainApp()
    ex.show()
    sys.exit(app.exec_())

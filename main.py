import sys
from PyQt5.QtWidgets import QApplication, QWidget
from csv_viewer import CSVViewer
from pandas_model import PandasModel
from table_manager import TableManager
import numpy as np
import pandas as pd
from math_operations import MathOperations
from ui import UIInitializer 

# Импортируем matplotlib и применяем стиль
import matplotlib.pyplot as plt
import scienceplots
plt.style.use(['science', 'no-latex', 'notebook', 'grid'])


class MainApp(QWidget): 
    """Главное приложение."""
    
    def __init__(self):
        """Инициализация класса."""
        super().__init__()

        self.viewer = CSVViewer()
        self.tableManager = TableManager(self.viewer)
        self.tableManager.gaussian_model.dataChangedSignal.connect(self.rebuildGaussians)
        self.math_operations = MathOperations()
        self.uiInitializer = UIInitializer(self)

    def getCSV(self):
        """Получение данных из CSV."""
        self.viewer.getCSV()
        self.tableManager.fillComboBoxes(self.uiInitializer.comboBoxX, self.uiInitializer.comboBoxY)
        self.tableManager.fillTable()

    def interactiveMode(self, activated):
        """Интерактивный режим."""
        if activated:
            self.tableManager.stacked_widget.setCurrentIndex(1)
            self.press_cid = self.uiInitializer.canvas.mpl_connect('button_press_event', self.on_press)
            self.release_cid = self.uiInitializer.canvas.mpl_connect('button_release_event', self.on_release)
        else:
            self.tableManager.stacked_widget.setCurrentIndex(0)
            self.uiInitializer.canvas.mpl_disconnect(self.press_cid)
            self.uiInitializer.canvas.mpl_disconnect(self.release_cid)

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
        x_column_data = self.get_column_data(self.uiInitializer.comboBoxX.currentText())
        x = np.linspace(min(x_column_data), max(x_column_data), 1000)
        y = self.math_operations.gaussian(x, self.press_y, self.press_x, width)

        ax = self.uiInitializer.figure.get_axes()[0]
        ax.plot(x, y, 'r-')
        self.uiInitializer.canvas.draw()
        
        self.tableManager.add_gaussian_to_table(self.press_y, self.press_x, width)

    def rebuildGaussians(self):
        """Перестроение всех гауссиан по данным в таблице."""
        self.plotGraph()  # очистим график
        print("rebuildGaussians was called")
        ax = self.uiInitializer.figure.get_axes()[0]
        for _, row in self.tableManager.gaussian_data.iterrows():
            x_column_data = self.get_column_data(self.uiInitializer.comboBoxX.currentText())
            x = np.linspace(min(x_column_data), max(x_column_data), 1000)
            y = self.math_operations.gaussian(x, row['Height'], row['Center'], row['Width'])
            ax.plot(x, y, 'r-')

        self.uiInitializer.canvas.draw()

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
        """Добавление дифференцирования."""
        x_column = self.uiInitializer.comboBoxX.currentText()
        y_column = self.uiInitializer.comboBoxY.currentText()
        dy_dx = self.math_operations.compute_derivative(self.viewer.df[x_column], self.viewer.df[y_column])
        new_column_name = y_column + '_diff'        
        self.viewer.df[new_column_name] = dy_dx
        self.tableManager.fillTable()
        self.tableManager.fillComboBoxes(self.uiInitializer.comboBoxX, self.uiInitializer.comboBoxY)

    def deleteColumn(self):
        """Удаление колонки."""
        self.tableManager.deleteColumn(self.uiInitializer.comboBoxX, self.uiInitializer.comboBoxY, self.tableManager.stacked_widget.currentIndex())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainApp()
    ex.show()
    sys.exit(app.exec_())

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
        self.table_manager = TableManager(self.viewer, self.math_operations) # Было: tableManager
        self.ui_initializer = UIInitializer(self, self.viewer) # Было: uiInitializer

        # Инициализируем CSVViewer, передав в него ссылки на table_manager и ui_initializer
        self.viewer.initialize(self.table_manager, self.ui_initializer) # Было: tableManager, uiInitializer

        self.event_handler = EventHandler(self) # Было: eventHandler

        self.table_manager.gaussian_model.data_changed_signal.connect(self.rebuild_gaussians) # Было: dataChangedSignal, rebuildGaussians
        self.event_handler.connect_signals() # Было: connectSignals

    def switch_to_interactive_mode(self, activated): # Было: switchToInteractiveMode
        """Переключение на интерактивный режим."""
        if activated:
            self.event_handler.connect_canvas_events() # Было: connectCanvasEvents
        else:
            self.event_handler.disconnect_canvas_events() # Было: disconnectCanvasEvents

    def rebuild_gaussians(self): # Было: rebuildGaussians
        """Перестроение всех гауссиан по данным в таблице."""
        self.plot_graph()  # очистим график # Было: plotGraph
        ax = self.ui_initializer.figure.get_axes()[0] # Было: uiInitializer
        for _, row in self.table_manager.gaussian_data.iterrows(): # Было: tableManager
            x_column_data = self.table_manager.get_column_data(self.ui_initializer.combo_box_x.currentText()) # Было: tableManager, uiInitializer, comboBoxX
            x = np.linspace(min(x_column_data), max(x_column_data), 1000)
            if row['Type'] == 'gauss':
                y = self.math_operations.gaussian(x, row['Height'], row['Center'], row['Width'])
            else:
                y = self.math_operations.fraser_suzuki(x, row['Height'], row['Center'], row['Width'], -1)
            ax.plot(x, y, 'r-')

        self.ui_initializer.canvas.draw() # Было: uiInitializer

    def compute_peaks(self): # Было: computePeaks
        x_column = self.ui_initializer.combo_box_x.currentText() # Было: uiInitializer, comboBoxX
        y_column = self.ui_initializer.combo_box_y.currentText() # Было: uiInitializer, comboBoxY
        self.table_manager.compute_peaks(x_column, y_column) # Было: tableManager, computePeaks
        self.rebuild_gaussians() # Было: rebuildGaussians

    def plot_graph(self): # Было: plotGraph
        """Построение графика."""
        x_column = self.ui_initializer.combo_box_x.currentText() # Было: uiInitializer, comboBoxX
        y_column = self.ui_initializer.combo_box_y.currentText() # Было: uiInitializer, comboBoxY

        if not x_column or not y_column:  # Если одно из значений пустое, прекратить функцию
            return

        self.ui_initializer.figure.clear() # Было: uiInitializer

        ax = self.ui_initializer.figure.add_subplot(111) # Было: uiInitializer
        ax.plot(self.viewer.df[x_column], self.viewer.df[y_column], 'b-')

        self.ui_initializer.canvas.draw() # Было: uiInitializer

    def add_diff(self): # Было: addDiff
        x_column = self.ui_initializer.combo_box_x.currentText() # Было: uiInitializer, comboBoxX
        y_column = self.ui_initializer.combo_box_y.currentText() # Было: uiInitializer, comboBoxY
        self.table_manager.add_diff(x_column, y_column, self.ui_initializer.combo_box_x, self.ui_initializer.combo_box_y) # Было: tableManager, addDiff, uiInitializer, comboBoxX, comboBoxY

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainApp()
    ex.show()
    sys.exit(app.exec_())

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
        self.table_manager = TableManager(self.viewer, self.math_operations)
        self.ui_initializer = UIInitializer(self, self.viewer)

        # Инициализируем CSVViewer, передав в него ссылки на table_manager и ui_initializer
        self.viewer.initialize(self.table_manager, self.ui_initializer) 
        
        self.event_handler = EventHandler(self)
        self.table_manager.gaussian_model.data_changed_signal.connect(self.event_handler.rebuild_gaussians) 
        self.event_handler.connect_signals() 
        
    def switch_to_interactive_mode(self, activated):        
        if activated:
            self.event_handler.connect_canvas_events()
        else:
            self.event_handler.disconnect_canvas_events()

    def compute_peaks(self):        
        self.event_handler.compute_peaks_button_pushed()    

    def add_diff(self):        
        self.event_handler.add_diff_button_pushed()
        
    def plot_graph(self):
        self.event_handler.plot_graph()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainApp()
    ex.show()
    sys.exit(app.exec_())

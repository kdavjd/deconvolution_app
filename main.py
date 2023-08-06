import sys
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QVBoxLayout, QLabel, QPushButton, QDoubleSpinBox
from PyQt5.QtCore import Qt
from src.csv_viewer import CSVViewer
from src.pandas_model import PandasModel
from src.table_manager import TableManager
import numpy as np
import pandas as pd
from src.math_operations import MathOperations
from src.ui import UIInitializer
from src.event_handler import EventHandler

# Импортируем matplotlib и применяем стиль
import matplotlib.pyplot as plt
import scienceplots
plt.style.use(['science', 'no-latex', 'notebook', 'grid'])

    
class MainApp(QWidget):
    """Главное приложение."""
    functions_data = pd.DataFrame(columns=['reaction', 'height', 'center', 'width', 'type', 'coeff_1'])
    options_data = pd.DataFrame({'maxfev': [2000], 'coeff_': [-1]})
    table_dict = {'gauss':functions_data,
                  'options':options_data}
    
    def __init__(self):
        """Инициализация класса."""
        super().__init__()

        self.frazer_a3 = -1
        self.maxfev = 1000
        # Создаем экземпляры без аргументов
        self.viewer = CSVViewer(table_dict=self.table_dict)
        self.math_operations = MathOperations()
        
        # Создаем другие объекты, передавая в них ссылку на viewer
        self.table_manager = TableManager(self.viewer, self.math_operations, [*self.table_dict.keys()], self.table_dict)
        self.ui_initializer = UIInitializer(self, self.viewer)

        # Инициализируем CSVViewer, передав в него ссылки на table_manager и ui_initializer
        self.viewer.initialize(self.table_manager, self.ui_initializer) 
        
        self.event_handler = EventHandler(self)
        self.table_manager.models['gauss'].data_changed_signal.connect(self.event_handler.rebuild_gaussians) 
        self.event_handler.connect_signals()
    
    def load_csv_table(self):
        self.viewer.get_csv()
        self.table_dict.update({self.viewer.file_name: self.viewer.df})
        
        # Удаление всех ключей со значением None
        self.table_dict = {k: v for k, v in self.table_dict.items() if k is not None}
        
        print(f"Current table dict keys before TableManager init: {self.table_dict.keys()}")        
        
        self.table_manager.update_table_data(self.viewer.file_name, self.viewer.df)
        
        print(f"TableManager instance created.")
        
        print(self.table_dict.keys())
        self.table_manager.fill_table(self.viewer.file_name)       
    
    def switch_to_interactive_mode(self, activated):
        if activated:
            self.event_handler.connect_canvas_events()
        else:
            self.event_handler.disconnect_canvas_events()

    def options_mode(self):        
        pass
    
    def compute_peaks(self):        
        self.event_handler.compute_peaks_button_pushed()    

    def add_diff(self):        
        self.event_handler.add_diff_button_pushed()
        
    def plot_graph(self):
        self.event_handler.plot_graph()
        
    def create_new_table():
        
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainApp()
    ex.show()
    sys.exit(app.exec_())

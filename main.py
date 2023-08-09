import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtCore import Qt
from src.csv_viewer import CSVViewer
from src.pandas_model import PandasModel
from src.table_manager import TableManager
import numpy as np
import pandas as pd
from src.math_operations import MathOperations
from src.ui import UIInitializer
from src.event_handler import EventHandler
import logging
from scipy.optimize import minimize

# Импортируем matplotlib и применяем стиль
import matplotlib.pyplot as plt
import scienceplots
plt.style.use(['science', 'no-latex', 'notebook', 'grid'])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
    
class MainApp(QMainWindow):
    """Главное приложение."""
    functions_data = pd.DataFrame(columns=['reaction', 'height', 'center', 'width', 'type', 'coeff_1'])
    options_data = pd.DataFrame({'maxfev': [2000], 'coeff_1': [-1], 'rmse':[0.0]})
    table_dict = {'gauss':functions_data,
                  'options':options_data}
    
    def __init__(self):
        """Инициализация класса."""
        super().__init__()
        
        # Создаем экземпляры без аргументов
        self.viewer = CSVViewer(table_dict=self.table_dict)
        self.math_operations = MathOperations()
        
        # Создаем другие объекты, передавая в них ссылку на viewer
        self.table_manager = TableManager(self.viewer, self.math_operations, [*self.table_dict.keys()], self.table_dict)
        self.ui_initializer = UIInitializer(self, self.viewer)
        self.setCentralWidget(self.ui_initializer.main_splitter)
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
        self.table_manager.update_table_data(self.viewer.file_name, self.viewer.df)
        self.table_manager.fill_table(self.viewer.file_name)       
    
    def switch_to_interactive_mode(self, activated):
        if activated:
            self.event_handler.connect_canvas_events()
        else:
            self.event_handler.disconnect_canvas_events()

    def options_mode(self):        
        self.table_manager.fill_table('options')
    
    def compute_peaks(self):
             
        def objective(coefficients):
            return self.event_handler.compute_peaks_button_pushed(coefficients)

        # Начальные значения коэффициентов
        initial_coefficients = [-1, -1]

        # Ограничения для коэффициентов
        constraints = [
            {'type': 'ineq', 'fun': lambda x: -0.01 - x[0]},
            {'type': 'ineq', 'fun': lambda x: x[0] + 4},
            {'type': 'ineq', 'fun': lambda x: -0.01 - x[1]},
            {'type': 'ineq', 'fun': lambda x: x[1] + 4},
        ]

        # Запускаем процесс оптимизации
        result = minimize(objective, initial_coefficients, constraints=constraints, method='SLSQP')

        # Лучшие значения коэффициентов
        best_coefficients = result.x

        logger.info(f'Лучшие значения коэффициентов = {best_coefficients}')
        self.event_handler.compute_peaks_button_pushed(best_coefficients)

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

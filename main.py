import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtCore import Qt, QThread, pyqtSignal
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

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ComputePeaksThread(QThread):
    progress_signal = pyqtSignal(float)
    finished_signal = pyqtSignal(object) # Для передачи результата

    def __init__(self, x_column_name, y_column_name, initial_coefficients, constraints, event_handler, table_manager, init_params):
        super().__init__()
        self.x_column_name = x_column_name
        self.y_column_name = y_column_name
        self.initial_coefficients = initial_coefficients
        self.constraints = constraints
        self.is_running = True
        self.event_handler = event_handler
        self.table_manager = table_manager
        self.init_params = init_params

    def run(self):
        def objective(coefficients):
            if not self.is_running:
                raise Exception("Остановка оптимизации по требованию пользователя")
            best_rmse = self.event_handler.data_handler.compute_peaks_button_pushed(
                coefficients, self.x_column_name, self.y_column_name, self.init_params)
            return best_rmse

        def callback(x):
            if not self.is_running:
                raise Exception("Остановка оптимизации по требованию пользователя")

        try:
            result = minimize(objective, self.initial_coefficients, constraints=self.constraints, method='SLSQP', callback=callback)
            if self.is_running:
                self.finished_signal.emit(result) # Передача результата
        except Exception as e:
            logger.warning(str(e))
            self.finished_signal.emit(None) # Передача None, если есть ошибка

    def stop(self):
        self.is_running = False
        
class MainApp(QMainWindow):
    """Главное приложение."""
    functions_data = pd.DataFrame(columns=['reaction', 'height', 'center', 'width', 'type', 'coeff_1'])
    options_data = pd.DataFrame({'maxfev': [1000], 'coeff_1': [-1], 'rmse':[0.0]})
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
        self.table_manager.models['gauss'].data_changed_signal.connect(self.event_handler.graph_handler.rebuild_gaussians) 
        self.event_handler.ui_handler.connect_signals()
        self.event_handler.update_console_signal.connect(self.ui_initializer.update_console)
        
        self.stop_optimization = False
    
    def load_csv_table(self):
        self.viewer.get_csv()
        self.table_dict.update({self.viewer.file_name: self.viewer.df})
        # Удаление всех ключей со значением None
        self.table_dict = {k: v for k, v in self.table_dict.items() if k is not None} 
        self.table_manager.update_table_data(self.viewer.file_name, self.viewer.df)
        self.table_manager.fill_table(self.viewer.file_name)
        box_list = [self.ui_initializer.combo_box_x, self.ui_initializer.combo_box_y]
        self.table_manager.fill_combo_boxes(self.viewer.file_name, box_list, True)
    
    def switch_to_interactive_mode(self, activated):
        if activated:
            self.event_handler.ui_handler.connect_canvas_events()
        else:
            self.event_handler.ui_handler.disconnect_canvas_events()

    def options_mode(self):        
        self.table_manager.fill_table_signal.emit('options')    
   
    def compute_peaks(self):
        x_column_name = self.ui_initializer.combo_box_x.currentText()
        y_column_name = self.ui_initializer.combo_box_y.currentText()

        if self.table_manager.data['gauss']['coeff_1'].size > 0:
            initial_coefficients = self.table_manager.data['gauss']['coeff_1'].values
            logger.debug(f'содержание initial_coefficients {initial_coefficients}')

            constraints = []
            for i in range(len(initial_coefficients)):
                constraints.append({'type': 'ineq', 'fun': lambda x, i=i: -0.01 - x[i]})
                constraints.append({'type': 'ineq', 'fun': lambda x, i=i: x[i] + 4})

            # Создание экземпляра потока
            init_params = self.event_handler.data_handler.get_init_params()
            self.compute_peaks_thread = ComputePeaksThread(
                x_column_name, y_column_name, initial_coefficients, constraints, 
                self.event_handler, self.table_manager, init_params)

            # Соединение сигналов с нужными слотами
            self.compute_peaks_thread.finished_signal.connect(self.on_peaks_computed)
            self.compute_peaks_thread.progress_signal.connect(self.on_progress_update)  # Если нужно обновление прогресса

            # Запуск потока
            self.compute_peaks_thread.start()

    def on_peaks_computed(self, result):
        if result:
            best_coefficients = result.x
            logger.info(f'Лучшие значения коэффициентов = {best_coefficients}')
            self.event_handler.data_handler.compute_peaks_button_pushed(
                best_coefficients, self.ui_initializer.combo_box_x.currentText(), self.ui_initializer.combo_box_y.currentText())
        else:
            logger.warning('Ошибка при вычислении пиков')

    def on_progress_update(self, progress):
        # Здесь можно обновить индикатор прогресса или другие элементы UI
        pass

    def stop_computing_peaks(self):
        self.compute_peaks_thread.stop()  # Останавливаем поток, если он запущен
        
    def add_diff(self):
        x_column_name = self.ui_initializer.combo_box_x.currentText() 
        y_column_name = self.ui_initializer.combo_box_y.currentText()     
        self.event_handler.data_handler.add_diff_button_pushed(x_column_name, y_column_name)
        
    def plot_graph(self):
        self.event_handler.graph_handler.plot_graph_signal.emit()
        
    def create_new_table():        
        pass
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainApp()
    ex.show()
    sys.exit(app.exec_())

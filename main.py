import sys
from io import StringIO
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from src.csv_viewer import CSVViewer
from src.pandas_model import PandasModel
from src.table_manager import TableManager
from src.math_operations import MathOperations
from src.ui import UIInitializer
from src.event_handler import EventHandler
import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution
import pathlib
# Импортируем matplotlib и применяем стиль
import matplotlib.pyplot as plt
import scienceplots
plt.style.use(['science', 'no-latex', 'nature', 'grid'])

from src.logger_config import logger


class ComputePeaksThread(QThread):
    progress_signal = pyqtSignal(float)
    finished_signal = pyqtSignal(object)

    def __init__(self, event_handler, peaks_params, combinations, extracted_bounds, peaks_bounds, selected, options):
        super().__init__()        
        self.is_running = True
        self.event_handler = event_handler        
        self.peaks_params = peaks_params
        self.combinations = combinations
        self.extracted_bounds = extracted_bounds        
        self.peaks_bounds = peaks_bounds
        self.selected = selected
        self.options = options

    def run(self):
        def objective(coefficients):
            if not self.is_running:
                raise Exception("Остановка оптимизации по требованию пользователя")
            best_rmse = self.event_handler.data_handler.compute_peaks_button_pushed(
                coefficients, self.selected, self.peaks_params, self.combinations, self.peaks_bounds)
            return best_rmse

        def callback(x):
            if not self.is_running:
                raise Exception("Остановка оптимизации по требованию пользователя")
        
        try:
            result = differential_evolution(
                objective, 
                self.extracted_bounds, 
                strategy=self.options['strategy'].values.item(), 
                popsize=int(self.options['popsize'].values.item()), 
                recombination=float(self.options['recombination'].values.item()),
                mutation=float(self.options['mutation'].values.item()), 
                tol=float(self.options['tol'].values.item()), 
                maxiter=int(self.options['maxiter'].values.item())
            )
            if self.is_running:
                self.finished_signal.emit(result)
        
        except Exception as e:
            logger.warning(str(e))
            self.event_handler.data_handler.console_message_signal.emit(
                f'\nОшибка в функции оптимизации\n {e}')
            self.finished_signal.emit(None) # Передача None, если есть ошибка

    def stop(self):
        self.is_running = False
        
class MainApp(QMainWindow):
    """Главное приложение."""
    functions_data = pd.DataFrame(columns=[
        'reaction', 'height', 'center', 'width', 'type', 'coeff_a'])
    
    options_data = pd.DataFrame({
        'maxfev': [1000], 'popsize': [5], 'maxiter': [5], 'recombination': [0.9], 'coeff_s2': [1], 'mutation':[0.7], 
        'tol':[0.1], 'strategy':['best2bin'], 'rmse':[0.0], 'window_length':[11],'polyorder':[3], 'Savitzky_mode':['nearest'],
        'coeff_a': [-0.01], 'coeff_s1': [1], 'coeff_s2': [1], 
        'rmse':[1000], 'a_bottom_constraint':[-4], 'a_top_constraint':[-0.01], 
        's1_bottom_constraint':[0], 's1_top_constraint':[10],
        's2_bottom_constraint':[0], 's2_top_constraint':[10],})
    
    table_dict = {
        'gauss':functions_data,'options':options_data}
    
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
        # Сохранение информации DataFrame в строке
        buffer = StringIO()
        self.viewer.df.info(buf=buffer)
        file_info = buffer.getvalue()
        self.event_handler.data_handler.console_message_signal.emit(f'Загружен CSV файл:\n {file_info}')
        bp = pathlib.Path().absolute() / 'logs_folder'
        bp.mkdir(exist_ok=True, parents=True)
        file_handler = logging.FileHandler(bp / f'{self.viewer.file_name}.log')
        logger.addHandler(file_handler)
    
    def switch_to_interactive_mode(self, activated):
        if activated:
            self.event_handler.ui_handler.connect_canvas_events()
        else:
            self.event_handler.ui_handler.disconnect_canvas_events()

    def options_mode(self):        
        self.table_manager.fill_table_signal.emit('options')    
   
    def compute_peaks(self):
        selected, combinations, coeffs_bounds, peaks_bounds_dict = self.event_handler.calculation_dialog_handler.fetch_peak_type_and_bounds()
        if not selected:
            return
        extracted_bounds = self.event_handler.calculation_dialog_handler.extract_bounds_selected_combinations(selected, coeffs_bounds)
        peaks_bounds = self.event_handler.calculation_dialog_handler.extract_peaks_bounds(peaks_bounds_dict)        
        peaks_params = self.event_handler.data_handler.get_peaks_params()        
        
        self.compute_peaks_thread = ComputePeaksThread(self.event_handler, peaks_params, combinations, extracted_bounds, peaks_bounds, selected, self.table_manager.data['options'])

        # Соединение сигналов с нужными слотами
        self.compute_peaks_thread.finished_signal.connect(self.on_peaks_computed)
        self.compute_peaks_thread.progress_signal.connect(self.on_progress_update)

        # Запуск потока
        self.compute_peaks_thread.start()

    def on_peaks_computed(self, result):
        if result:
            best_coefficients = result.x
            logger.info(f'Лучшие значения коэффициентов = {best_coefficients}')
            self.event_handler.data_handler.console_message_signal.emit(
                f'Оптимизация завершена. Лучшие параметры:\n {best_coefficients}')
        else:
            logger.warning('Ошибка при вычислении пиков')

    def on_progress_update(self, progress):
        # Здесь можно обновить индикатор прогресса или другие элементы UI
        pass

    def stop_computing_peaks(self):
        self.event_handler.data_handler.console_message_signal.emit(
                f'\nОстановка вычислений. Дождитесь завершения потоков.\n')
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

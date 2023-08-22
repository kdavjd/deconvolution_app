from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal
from .graph_handler import GraphHandler
import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DataHandler(QObject):
    console_message_signal = pyqtSignal(str)
    refresh_gui_signal = pyqtSignal()
    
    def __init__(self, main_app):
       
        super().__init__()
        self.main_app = main_app
        # Инициализация основных компонентов главного приложения
        self.viewer = main_app.viewer
        self.table_manager = main_app.table_manager
        self.math_operations = main_app.math_operations
        self.ui_initializer = main_app.ui_initializer
        self.graph_handler = GraphHandler(main_app)
        
        self.received_data = None
        self.table_manager.column_data_returned_signal.connect(self.store_received_data)
        self.table_manager.get_data_returned_signal.connect(self.store_received_data)
        self.console_message_signal.connect(self.ui_initializer.update_console)
        self.refresh_gui_signal.connect(self.ui_initializer.refresh_gui)
    
    def store_received_data(self, data):
        self.received_data = data
        
    def add_diff_button_pushed(self, x_column_name: str, y_column_name: str):
        # Вычисление производной
        self.table_manager.get_column_data_signal.emit(self.viewer.file_name, x_column_name)
        x_values = self.received_data      
        
        self.table_manager.get_column_data_signal.emit(self.viewer.file_name, y_column_name)
        y_values = self.received_data
        
        dy_dx = self.math_operations.compute_derivative(x_values, y_values)

        # Добавление нового столбца с производной в DataFrame
        new_column_name = y_column_name + '_diff'
        self.table_manager.add_column_signal.emit(self.viewer.file_name, new_column_name, dy_dx)

        # Обновление интерфейса: заполнение таблицы и комбо-боксов
        self.table_manager.fill_table_signal.emit(self.viewer.file_name)
        
        box_list = [self.ui_initializer.combo_box_x, self.ui_initializer.combo_box_y]
        self.table_manager.fill_combo_boxes_signal.emit(self.viewer.file_name, box_list, False) 

        # Установка нового столбца как текущего для Y в комбо-боксе
        self.ui_initializer.combo_box_y.setCurrentText(new_column_name)

    def get_init_params(self):        
        logger.debug("Начало метода get_init_params.")
        self.table_manager.get_data_signal.emit('gauss')
        gaussian_data = self.received_data    
        
        init_params = []
        for index, row in gaussian_data.iterrows():
            logger.debug(f"Обработка строки {index}: height={row['height']}, center={row['center']}, width={row['width']}")
            init_params.extend([row['height'], row['center'], row['width']])
        logger.debug(f"Длина начальных параметров: {len(init_params)}")
        logger.debug(f"Конец метода get_init_params. Полученные параметры: {str(init_params)}.")
        return init_params
    
    def update_gaussian_data(self, best_params, best_combination, coeff_1):        
        logger.debug("Начало метода update_gaussian_data.")
        self.table_manager.get_data_signal.emit('gauss')
        gaussian_data = self.received_data
        
        for i, peak_type in enumerate(best_combination):
            height = best_params[3 * i]
            center = best_params[3 * i + 1]
            width = best_params[3 * i + 2]
            coeff_ = coeff_1[i]

            gaussian_data.at[i, 'height'] = height
            gaussian_data.at[i, 'center'] = center
            gaussian_data.at[i, 'width'] = width
            gaussian_data.at[i, 'type'] = peak_type
            gaussian_data.at[i, 'coeff_1'] = coeff_

        return gaussian_data
    
    def compute_peaks_button_pushed(self, coeff_1: list[float], x_column_name: str, y_column_name: str, best_rmse=None):
        
        coefficients_str = ', '.join(map(str, coeff_1))
        self.console_message_signal.emit(f'Получены коэффициенты: {coefficients_str}')      

        logger.info(f'Получены коэффициенты: {str(coeff_1)}')
        init_params = self.get_init_params()
        
        self.table_manager.get_column_data_signal.emit(self.viewer.file_name, x_column_name)
        x_values = self.received_data      
        
        self.table_manager.get_column_data_signal.emit(self.viewer.file_name, y_column_name)
        y_values = self.received_data
        
        self.table_manager.get_data_signal.emit('options')
        options_data = self.received_data
        
        maxfev = int(options_data['maxfev'].values)
        
        num_peaks = len(init_params) // 3
        if best_rmse is None:
            best_params, best_combination, best_rmse = self.math_operations.compute_best_peaks(
                x_values, y_values, num_peaks, init_params, maxfev, coeff_1)  
                
        best_gaussian_data = self.update_gaussian_data(best_params, best_combination, coeff_1)
        self.table_manager.update_table_signal.emit('gauss', best_gaussian_data)
            
        self.console_message_signal.emit(f'Лучшее RMSE: {best_rmse:.5f}')
        self.console_message_signal.emit(f'Лучшая комбинация пиков: {best_combination}')
        
        self.refresh_gui_signal.emit()
            
        cumulative_func = np.zeros(len(x_values)) 
        self.table_manager.add_reaction_cumulative_func_signal.emit(best_params, best_combination, x_values, y_column_name, cumulative_func)
            
        options_data['rmse'] = best_rmse
        self.table_manager.update_table_signal.emit('options', options_data)
        
        self.graph_handler.rebuild_gaussians_signal.emit()
            
        self.table_manager.fill_table_signal.emit('gauss')
            
        return best_rmse
    
    
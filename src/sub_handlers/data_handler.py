from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal
from .graph_handler import GraphHandler
import numpy as np
import logging
from time import sleep

from src.logger_config import logger

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
    
    def wait_for_data(self):
        while self.received_data is None:
            sleep(0.1) # Ждем 100 мс и проверяем снова
        return self.received_data
    
    def store_received_data(self, data):
        self.received_data = data
        
    def add_diff_button_pushed(self, x_column_name: str, y_column_name: str):
        # Вычисление производной
        self.table_manager.get_column_data_signal.emit(self.viewer.file_name, x_column_name)
        x_values = self.wait_for_data()      
        self.received_data = None        
        
        self.table_manager.get_column_data_signal.emit(self.viewer.file_name, y_column_name)
        y_values = self.wait_for_data()
        self.received_data = None
        
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
        self.table_manager.get_data_signal.emit('gauss')
        gaussian_data = self.wait_for_data()
        self.received_data = None
        logger.debug(f"Полученные данные в get_init_params: \n {gaussian_data}")
        
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
        gaussian_data = self.wait_for_data()
        self.received_data = None
        
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
    
    def compute_peaks_button_pushed(
        self, coeff_1: list[float], x_column_name: str, y_column_name: str, params: list, best_rmse=None):
           
        logger.info(f'Получены параметры: {params}')
        logger.debug(f'x_column_name:\n {x_column_name}')  
        logger.debug(f'self.received_data:\n {self.received_data}')
        
        # Округление коэффициентов до 5-го знака и отправка их в логи
        rounded_coeff_1 = [round(coeff, 5) for coeff in coeff_1]
        logger.info(f'Получены коэффициенты: {str(rounded_coeff_1)}\n')  
        
        self.table_manager.get_column_data_signal.emit(self.viewer.file_name, x_column_name)
        x_values = self.wait_for_data()
        logger.debug(f'x_values: {self.received_data}')
        self.received_data = None  
        
        self.table_manager.get_column_data_signal.emit(self.viewer.file_name, y_column_name)
        y_values = self.wait_for_data()
        logger.debug(f'y_values: {self.received_data}')
        self.received_data = None
        
        self.table_manager.get_data_signal.emit('options')
        options_data = self.wait_for_data()
        logger.debug(f'options_data: {options_data}')
        self.received_data = None
        
        maxfev = int(options_data['maxfev'].values)
        
        num_peaks = len(params) // 3
        if best_rmse is None:
            best_params, best_combination, best_rmse = self.math_operations.compute_best_peaks(
                x_values, y_values, num_peaks, params, maxfev, coeff_1, self.console_message_signal)  
                
        best_gaussian_data = self.update_gaussian_data(best_params, best_combination, coeff_1)
        self.table_manager.update_table_signal.emit('gauss', best_gaussian_data)
            
        self.console_message_signal.emit(f'Лучшее RMSE: {best_rmse:.5f}\n')
        self.console_message_signal.emit(f'Лучшая комбинация пиков: {best_combination}\n\n')
        
        self.refresh_gui_signal.emit()
            
        cumulative_func = np.zeros(len(x_values)) 
        self.table_manager.add_reaction_cumulative_func_signal.emit(best_params, best_combination, x_values, y_column_name, cumulative_func)
            
        options_data['rmse'] = best_rmse
        self.table_manager.update_table_signal.emit('options', options_data)
        
        self.graph_handler.rebuild_gaussians_signal.emit()
            
        self.table_manager.fill_table_signal.emit('gauss')
            
        return best_rmse
    
    
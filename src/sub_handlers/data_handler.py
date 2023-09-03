from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal
from .graph_handler import GraphHandler
from itertools import product
import numpy as np
import logging
from time import sleep
from functools import partial

from src.logger_config import logger

class DataHandler(QObject):
    console_message_signal = pyqtSignal(str)
    refresh_gui_signal = pyqtSignal()
    
    def __init__(self, main_app):
        super().__init__()
        self.initialize_components(main_app)
        self.connect_signals()

    def initialize_components(self, main_app):
        self.main_app = main_app
        self.viewer = main_app.viewer
        self.table_manager = main_app.table_manager
        self.math_operations = main_app.math_operations
        self.ui_initializer = main_app.ui_initializer
        self.graph_handler = GraphHandler(main_app)
        self.received_data = None
    
    def connect_signals(self):
        self.table_manager.column_data_returned_signal.connect(self.store_received_data)
        self.table_manager.get_data_returned_signal.connect(self.store_received_data)
        self.console_message_signal.connect(self.ui_initializer.update_console)
        self.refresh_gui_signal.connect(self.ui_initializer.refresh_gui)
        
    def store_received_data(self, data):
        self.received_data = data
             
    def wait_for_data(self):
        while self.received_data is None:
            sleep(0.1) # Ждем 100 мс и проверяем снова
        return self.received_data
    
    def retrieve_table_data(self, table_name):
        self.table_manager.get_data_signal.emit(table_name)
        data = self.wait_for_data()
        self.received_data = None
        return data
      
    def retrieve_column_data(self, table_name, column_name):
        self.table_manager.get_column_data_signal.emit(table_name, column_name)
        data = self.wait_for_data()
        self.received_data = None
        return data
    
    def add_diff_button_pushed(self, x_column_name: str, y_column_name: str):
        # Вычисление производной
        x_values = self.retrieve_column_data(self.viewer.file_name, x_column_name)
        y_values = self.retrieve_column_data(self.viewer.file_name, y_column_name)        
        dy_dx = self.math_operations.compute_derivative(x_values, y_values)
        self.update_data_after_add_diff(dy_dx, y_column_name)

    def update_data_after_add_diff(self, derivative_array, y_column_name):
        new_column_name = f"{y_column_name}_diff"
        self.table_manager.add_column_signal.emit(
            self.viewer.file_name, new_column_name, derivative_array)
        self.update_ui_after_add_diff(new_column_name)

    def update_ui_after_add_diff(self, new_column_name):
        self.table_manager.fill_table_signal.emit(self.viewer.file_name)
        box_list = [self.ui_initializer.combo_box_x, self.ui_initializer.combo_box_y]
        self.table_manager.fill_combo_boxes_signal.emit(
            self.viewer.file_name, box_list, False)
        self.ui_initializer.combo_box_y.setCurrentText(new_column_name)
    
    def get_init_params(self):        
        gaussian_data = self.retrieve_table_data('gauss')        
        logger.info(f"Полученные данные в get_init_params: \n {gaussian_data}")
        
        init_params = []
        for index, row in gaussian_data.iterrows():
            logger.debug(f"Обработка строки {index}: height={row['height']}, center={row['center']}, width={row['width']}")
            init_params.extend([row['height'], row['center'], row['width']]) 
        return init_params
    
    def update_gaussian_data(self, best_params, best_combination, coeff_a, s1, s2):        
        gaussian_data = self.retrieve_table_data('gauss')
                
        for i, peak_type in enumerate(best_combination):
            height = best_params[3 * i]
            center = best_params[3 * i + 1]
            width = best_params[3 * i + 2]
            coeff_ = coeff_a[i]
            coeff_s1 = s1[i]
            coeff_s2 = s2[i]

            gaussian_data.at[i, 'height'] = height
            gaussian_data.at[i, 'center'] = center
            gaussian_data.at[i, 'width'] = width
            gaussian_data.at[i, 'type'] = peak_type
            gaussian_data.at[i, 'coeff_a'] = coeff_
            gaussian_data.at[i, 'coeff_s1'] = coeff_s1
            gaussian_data.at[i, 'coeff_s2'] = coeff_s2

        return gaussian_data
    
    def calculate_gaussian_bounds(self, initial_params):
            lower_bounds = []
            upper_bounds = []

            # Деление initial_params на участки по 3 элемента
            for i in range(0, len(initial_params), 3):
                group = initial_params[i:i+3]

                # Для первого элемента группы: от 0 до +50%
                lower_bounds.append(group[0] * 0)
                upper_bounds.append(group[0] * 1.5)
                
                # Для второго элемента группы: от -20% до +20%
                lower_bounds.append(group[1] * 0.80)
                upper_bounds.append(group[1] * 1.20)

                # Для третьего элемента группы: от -40% до +40%
                lower_bounds.append(group[2] * 0.6)
                upper_bounds.append(group[2] * 1.4)

            return (lower_bounds, upper_bounds)
    
    def retrieve_and_log_data(self, table_name, column_name):
        data = self.retrieve_column_data(self.viewer.file_name, column_name)
        logger.debug(f"Полученные данные для {table_name}: \n {data}")
        return data

    def update_ui_and_data(self, best_params, best_combination, coeff_a, 
                           s1, s2, best_rmse, x_values, y_column_name, coefficients):
        
        best_gaussian_data = self.update_gaussian_data(
            best_params, best_combination, coeff_a, s1, s2)
        
        self.table_manager.update_table_signal.emit('gauss', best_gaussian_data)
        self.console_message_signal.emit(f'Лучшее RMSE: {best_rmse:.5f}\n')
        self.console_message_signal.emit(f'Лучшая комбинация пиков: {best_combination}\n\n')
        self.refresh_gui_signal.emit()

        cumulative_func = np.zeros(len(x_values)) 
        self.table_manager.add_reaction_cumulative_func_signal.emit(
            best_params, best_combination, x_values, y_column_name, cumulative_func, coefficients)

    def compute_peaks_button_pushed(
        self, coefficients: list[float], x_column_name: str, y_column_name: str, params: list, selected_peak_types: list[str], best_rmse=None):
        
        logger.debug(f"Начало compute_peaks_button_pushed: params: {params}")        
        logger.debug(f"coefficients: {coefficients}\n bounds: {bounds}")        
        x_values = self.retrieve_and_log_data('x_values', x_column_name)
        y_values = self.retrieve_and_log_data('y_values', y_column_name)
        bounds = self.calculate_gaussian_bounds(params) 
        options_data = self.retrieve_table_data('options')          
        maxfev = int(options_data['maxfev'].values)
        
        n = len(coefficients) // 3
        coeff_a, s1, s2 = coefficients[:n], coefficients[n:2*n], coefficients[2*n:]
        
        peak_types = ['gauss', 'fraser', 'ads']
        combinations = list(product(peak_types, repeat=n)) 
            
        if best_rmse is None:
            best_params, best_combination, best_rmse = self.math_operations.compute_best_peaks(
                x_values, y_values, n, params, maxfev, coeff_a, s1, s2, combinations, bounds, self.console_message_signal)

        self.update_ui_and_data(best_params, best_combination, coeff_a, s1, s2, best_rmse, x_values, y_column_name, coefficients)

        return best_rmse

    def get_coeffs_and_bounds(self, selected_peak_types):
        logger.debug('Вызов функции get_coeffs_and_bounds')
        logger.debug(f'Аргумент selected_peak_types: {selected_peak_types}')

        coeffs_dict = {}
        bounds_dict = {}

        if 'fraser' in selected_peak_types:
            logger.debug("Обработка типа 'fraser'")
            coeffs_dict['a'] = self.table_manager.data['gauss']['coeff_a'].values
            bounds_dict['a'] = (float(self.table_manager.data['options']['a_bottom_constraint'].iloc[0]),
                                float(self.table_manager.data['options']['a_top_constraint'].iloc[0]))
            logger.debug(f"coeffs_dict['a']: {coeffs_dict['a']}")
            logger.debug(f"bounds_dict['a']: {bounds_dict['a']}")

        if 'ads' in selected_peak_types:
            logger.debug("Обработка типа 'ads'")
            coeffs_dict['s1'] = self.table_manager.data['gauss']['coeff_s1'].values
            bounds_dict['s1'] = (float(self.table_manager.data['options']['s1_bottom_constraint'].iloc[0]),
                                float(self.table_manager.data['options']['s1_top_constraint'].iloc[0]))

            coeffs_dict['s2'] = self.table_manager.data['gauss']['coeff_s2'].values
            bounds_dict['s2'] = (float(self.table_manager.data['options']['s2_bottom_constraint'].iloc[0]),
                                float(self.table_manager.data['options']['s2_top_constraint'].iloc[0]))
            
            logger.debug(f"coeffs_dict['s1']: {coeffs_dict['s1']}")
            logger.debug(f"bounds_dict['s1']: {bounds_dict['s1']}")
            logger.debug(f"coeffs_dict['s2']: {coeffs_dict['s2']}")
            logger.debug(f"bounds_dict['s2']: {bounds_dict['s2']}")

        current_coeffs = np.array([])
        bounds = []
        for coeff_type, coeffs in coeffs_dict.items():
            logger.debug(f"Обработка coeff_type: {coeff_type}")
            current_coeffs = np.concatenate([current_coeffs, coeffs])
            bottom, top = bounds_dict[coeff_type]
            for i in range(len(coeffs)):
                bounds.append((bottom, top))

        logger.debug(f"Возвращаемые current_coeffs: {current_coeffs}")
        logger.debug(f"Возвращаемые bounds: {bounds}")

        return current_coeffs, bounds


    
    
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from .graph_handler import GraphHandler
from itertools import product
import numpy as np
import pandas as pd
import logging
from time import sleep
import uuid

from src.logger_config import logger

class DataHandler(QObject):
    console_message_signal = pyqtSignal(str)
    refresh_gui_signal = pyqtSignal()
    
    def __init__(self, main_app):
        super().__init__()
        self.initialize_components(main_app)
        self.connect_signals()
        self.pending_data_requests = {}

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
    
    def store_received_data(self, data, request_id):
        self.pending_data_requests[request_id] = data
               
    def wait_for_data(self, request_id):
        while request_id not in self.pending_data_requests:
            sleep(0.05) # Ждем 50 мс и проверяем снова
        data = self.pending_data_requests.pop(request_id)  # получаем и удаляем данные по ключу
        return data
    
    def retrieve_table_data(self, table_name: str) -> pd.DataFrame:
        request_id = uuid.uuid4()  
        self.table_manager.get_data_signal.emit(table_name, request_id)  
        data = self.wait_for_data(request_id)
        return data
      
    def retrieve_column_data(self, table_name: str, column_name: str) -> pd.Series:
        request_id = uuid.uuid4()  
        self.table_manager.get_column_data_signal.emit(table_name, column_name, request_id)
        data = self.wait_for_data(request_id)
        return data
    
    def retrieve_and_log_data(self, table_name: str, column_name: str, var_name: str) -> pd.Series:
        request_id = uuid.uuid4()
        self.table_manager.get_column_data_signal.emit(table_name, column_name, request_id)
        data = self.wait_for_data(request_id)
        logger.debug(f"Полученные данные для {var_name}: \n {data}")
        return data
    
    def add_diff_button_pushed(self, x_column_name: str, y_column_name: str):
        # Вычисление производной
        x_values = self.retrieve_column_data(self.viewer.file_name, x_column_name)
        y_values = self.retrieve_column_data(self.viewer.file_name, y_column_name)        
        dy_dx = self.math_operations.compute_derivative(x_values, y_values)
        self.update_data_after_add_diff(dy_dx, y_column_name)

    def update_data_after_add_diff(self, derivative_array: np.array, y_column_name: str):
        new_column_name = f"{y_column_name}_diff"
        self.table_manager.add_column_signal.emit(
            self.viewer.file_name, new_column_name, derivative_array)
        self.update_ui_after_add_diff(new_column_name)

    def update_ui_after_add_diff(self, new_column_name: str):
        self.table_manager.fill_table_signal.emit(self.viewer.file_name)
        box_list = [self.ui_initializer.combo_box_x, self.ui_initializer.combo_box_y]
        self.table_manager.fill_combo_boxes_signal.emit(
            self.viewer.file_name, box_list, False)
        self.ui_initializer.combo_box_y.setCurrentText(new_column_name)
    
    def get_peaks_params(self):        
        gaussian_data = self.retrieve_table_data('gauss')        
        logger.info(f"Полученные данные в get_peaks_params: \n {gaussian_data}")
        
        peaks_params = []
        for index, row in gaussian_data.iterrows():
            logger.debug(f"Обработка строки {index}: height={row['height']}, center={row['center']}, width={row['width']}")
            peaks_params.extend([row['height'], row['center'], row['width']]) 
        return peaks_params
    
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
            best_params, best_combination, x_values, y_column_name, cumulative_func, coeff_a, s1, s2)
        
        self.graph_handler.rebuild_gaussians_signal.emit()

    def modify_gauss_dataframe(self, selected_combinations: dict, coefficients: list[float]) -> pd.DataFrame:
        coefficients = coefficients.tolist()
        gaussian_data = self.retrieve_table_data('gauss')
        logger.debug(f'Получен gaussian_data: {gaussian_data}')
        
        for index, row in gaussian_data.iterrows():
            reaction = row['reaction']
            if reaction in selected_combinations:
                if 'fraser' in selected_combinations[reaction]:
                    gaussian_data.at[index, 'coeff_a'] = coefficients.pop(0)
                if 'ads' in selected_combinations[reaction]:
                    gaussian_data.at[index, 'coeff_s1'] = coefficients.pop(0)
                    gaussian_data.at[index, 'coeff_s2'] = coefficients.pop(0)
        
        self.table_manager.update_table_signal.emit('gauss', gaussian_data)
    
    def compute_peaks_button_pushed(
        self, coefficients: list[float], selected: dict, peaks_params: list[float], combinations: list[tuple[str,...]], peaks_bounds: list[tuple[float, float]]) -> float:
        logger.debug(f'Получены coefficients: {coefficients}')
              
        self.modify_gauss_dataframe(selected, coefficients)  
        
        x_column_name = self.ui_initializer.combo_box_x.currentText()
        y_column_name = self.ui_initializer.combo_box_y.currentText()      
        x_values = self.retrieve_and_log_data(self.viewer.file_name, x_column_name, 'x_values').astype(float).to_list()
        y_values = self.retrieve_and_log_data(self.viewer.file_name, y_column_name, 'y_values').astype(float).to_list()
        coeff_a = self.retrieve_and_log_data('gauss', 'coeff_a', 'coeff_a').astype(float).to_list()
        s1 = self.retrieve_and_log_data('gauss', 'coeff_s1', 'coeff_s1').astype(float).to_list()
        s2 = self.retrieve_and_log_data('gauss', 'coeff_s2', 'coeff_s2').astype(float).to_list()
        maxfev = self.retrieve_and_log_data('options', 'maxfev', 'maxfev').astype(int).item()
                
        best_params, best_combination, best_rmse = self.math_operations.compute_best_peaks(
            x_values, y_values, peaks_params, maxfev, coeff_a, s1, s2, combinations, peaks_bounds, self.console_message_signal)

        self.update_ui_and_data(best_params, best_combination, coeff_a, s1, s2, best_rmse, x_values, y_column_name, coefficients)

        return best_rmse
    
    

    


    
    
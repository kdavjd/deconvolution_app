from time import sleep
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QTableView, QStackedWidget, QFileDialog
from PyQt5.QtCore import Qt, QObject, pyqtSlot
import pandas as pd
from src.pandas_model import PandasModel
import uuid
import os

from src.logger_config import logger

class TableManager(QObject):
    get_data_signal = pyqtSignal(str, uuid.UUID)
    get_data_returned_signal = pyqtSignal(pd.DataFrame, uuid.UUID)
    update_table_signal = pyqtSignal(str, pd.DataFrame)
    fill_table_signal = pyqtSignal(str)
    add_row_signal = pyqtSignal(str, pd.DataFrame)
    add_column_signal = pyqtSignal(str, str, object)
    delete_row_signal = pyqtSignal(int)
    delete_column_signal = pyqtSignal(int)
    fill_combo_boxes_signal = pyqtSignal(str, list, bool)
    get_column_data_signal = pyqtSignal(str, str, uuid.UUID)
    column_data_returned_signal = pyqtSignal(pd.Series, uuid.UUID)
    add_reaction_cumulative_func_signal = pyqtSignal(object, tuple, object, str, object, object, object, object)
    add_gaussian_to_table_signal = pyqtSignal(float, float, float)

    def __init__(self, viewer, math_operations, table_names, table_dict):
        super().__init__()
        # Инициализация сигналов
        self.get_data_signal.connect(self.get_data)
        self.update_table_signal.connect(self.update_table_data)
        self.fill_table_signal.connect(self.fill_table)
        self.add_row_signal.connect(self.add_row)
        self.add_column_signal.connect(self.add_column)
        self.delete_row_signal.connect(self.delete_row)
        self.delete_column_signal.connect(self.delete_column)
        self.fill_combo_boxes_signal.connect(self.fill_combo_boxes)
        self.get_column_data_signal.connect(self.get_column_data) 
        self.add_reaction_cumulative_func_signal.connect(self.add_reaction_cumulative_func)
        self.add_gaussian_to_table_signal.connect(self.add_gaussian_to_table)

        self.viewer = viewer
        self.math_operations = math_operations          
        self.table_names = table_names           
        self.data = {}
        self.models = {}
        self.tables = {}
        self.stacked_widget = QStackedWidget()
        self.table_indexes = {}
        self.current_table_name = None
        self.bufer_table_name = None
        
        for name in table_names:
            self.data[name] = table_dict[name]
            self.models[name] = PandasModel(self.data[name])
            self.tables[name] = QTableView()
            self.tables[name].setModel(self.models[name])
            self.stacked_widget.addWidget(self.tables[name])
            self.table_indexes[name] = self.stacked_widget.count() - 1  
        
        logger.info(f"Object ID at init: {id(self)} - table names: {self.table_names}")      
        
    @pyqtSlot(str, uuid.UUID)
    def get_data(self, table_name, request_id=None):
        if table_name not in self.table_names:
            raise ValueError(f"Неизвестное имя таблицы: {table_name}")
        
        data = self.data[table_name]
        logger.debug(f'Переданы данные из таблицы {table_name}: \n {data}')        
        
        if request_id:
            self.get_data_returned_signal.emit(data, request_id)
        else:
            self.get_data_returned_signal.emit(data, uuid.uuid4())
    
    @pyqtSlot(str, str, uuid.UUID)
    def get_column_data(self, table_name, column_name, request_id=None):
        logger.debug(f'get_column_data table_name: {table_name} column_name: {column_name} request_id: {request_id}')
        
        if table_name not in self.table_names:
            raise ValueError(f"Неизвестное имя таблицы: {table_name}")

        column_data = self.data[table_name][column_name]
        
        if pd.to_numeric(column_data, errors='coerce').notna().all():
            self.column_data_returned_signal.emit(column_data, request_id)            
        else:
            raise ValueError(f"Колонка {column_name} в таблице {table_name} содержит non-numeric данные")
    
    @pyqtSlot(str, pd.DataFrame)
    def update_table_data(self, table_name, data):
        if table_name not in self.table_names:
            self.table_names.append(table_name)
            self.table_indexes[table_name] = self.stacked_widget.count()
            self.tables[table_name] = QTableView()
            self.stacked_widget.addWidget(self.tables[table_name])
        
        self.data[table_name] = data
        self.models[table_name] = PandasModel(self.data[table_name])
        self.tables[table_name].setModel(self.models[table_name])
    
    @pyqtSlot(str)
    def fill_table(self, table_name):
        if table_name not in self.table_names:                      
            raise ValueError(f"Неизвестное имя таблицы: {table_name}")        

        # Обновляем буфер и текущую таблицу
        self.bufer_table_name = self.current_table_name
        self.current_table_name = table_name
            
        self.models[table_name] = PandasModel(self.data[table_name])        
        self.tables[table_name].setModel(self.models[table_name])

        self.tables[table_name].reset()

        index = self.table_indexes[table_name]
        self.stacked_widget.setCurrentIndex(index)
        self.tables[table_name].update()
        
    @pyqtSlot(str, str, object)
    def add_column(self, table_name, column_name, column_data):
        
        if table_name not in self.table_names:
            raise ValueError(f"Неизвестное имя таблицы: {table_name}")
        
        self.data[table_name][column_name] = column_data
        self.models[table_name] = PandasModel(self.data[table_name])
        self.tables[table_name].setModel(self.models[table_name])        

    @pyqtSlot(str, pd.DataFrame)
    def add_row(self, table_name, row_data):
        if table_name not in self.table_names:
            raise ValueError(f"Неизвестное имя таблицы: {table_name}")

        self.data[table_name] = pd.concat([self.data[table_name], row_data], ignore_index=True)
        self.fill_table(table_name)

    @pyqtSlot(str, list, bool)
    def fill_combo_boxes(self, table_name, combo_boxes, block_signals=False):
        if table_name not in self.table_names:
            raise ValueError(f"Неизвестное имя таблицы: {table_name}")
        
        columns = self.data[table_name].columns
        logger.debug(f'fill_combo_boxes table_name: {table_name}, columns: {columns}')
        
        for combo_box in combo_boxes:
            if block_signals:
                combo_box.blockSignals(True)
            combo_box.clear()
            combo_box.addItems(columns)
            if block_signals:
                combo_box.blockSignals(False)    

    @pyqtSlot(object, tuple, object, str, object, object, object, object)
    def add_reaction_cumulative_func(self, best_params, best_combination, x_values, y_column, cumulative_func, coeff_a, coeff_s1, coeff_s2):        
                
        for i, peak_type in enumerate(best_combination):
            a0 = best_params[3 * i]
            a1 = best_params[3 * i + 1]
            a2 = best_params[3 * i + 2]
            
            new_column_name = y_column + '_reaction_' + str(i)
            
            if peak_type == 'gauss':
                peak_func = self.math_operations.gaussian(x_values, a0, a1, a2)
            elif peak_type == 'fraser':
                peak_func = self.math_operations.fraser_suzuki(x_values, a0, a1, a2, coeff_a[i])
            elif peak_type == 'ads': 
                s1 = coeff_s1[i]
                s2 = coeff_s2[i]
                peak_func = self.math_operations.asymmetric_double_sigmoid(x_values, a0, a1, a2, s1, s2)
            
            self.data[self.viewer.file_name][new_column_name] = peak_func
            cumulative_func += peak_func

        new_column_name = y_column + '_cumulative'
        self.data[self.viewer.file_name][new_column_name] = cumulative_func

    
    @pyqtSlot(float, float, float)
    def add_gaussian_to_table(self, height, center, width):        
        self.gaus = self.data['gauss']
        row_data = pd.DataFrame({'reaction': [f'Reaction_{self.gaus.shape[0] + 1}'], 
                                 'height': [height],
                                 'center': [center],
                                 'width': [width],
                                 'type':['frazer'],
                                 'coeff_a': [float(self.data['options']['coeff_a'].values)],
                                 'coeff_s1': [float(self.data['options']['coeff_s1'].values)],
                                 'coeff_s2': [float(self.data['options']['coeff_s2'].values)]
                                 })
        self.data['gauss'] = pd.concat([self.gaus, row_data], ignore_index=True)
        self.models['gauss'] = PandasModel(self.gaus)
        self.tables['gauss'].setModel(self.models['gauss'])
        self.fill_table_signal.emit('gauss')

    @pyqtSlot(int)
    def delete_row(self, row_number):               
        self.data[self.current_table_name] = self.data[self.current_table_name].drop(self.data[self.current_table_name].index[row_number])
        self.models[self.current_table_name] = PandasModel(self.data[self.current_table_name])
        self.tables[self.current_table_name].setModel(self.models[self.current_table_name])        

    @pyqtSlot(int)
    def delete_column(self, column_number):              
        column_name = self.data[self.current_table_name].columns[column_number]        
        self.data[self.current_table_name] = self.data[self.current_table_name].drop(columns=[column_name])
        self.models[self.current_table_name] = PandasModel(self.data[self.current_table_name])
        self.tables[self.current_table_name].setModel(self.models[self.current_table_name])  
                
    def save_table_to_csv(self, table_name='gauss'):
        logger.info('Метод save_table_to_csv вызван.') 
        
        if table_name in self.data.keys():            
            logger.info(f'Таблица {table_name} существует в области видимости.')
            df_to_save = self.data[table_name]            
            
            logger.info(f'Сохраняем следующий DataFrame: {df_to_save.head()}') 
            file_name, _ = QFileDialog.getSaveFileName(None, 'Save CSV', os.getenv('HOME'), 'CSV(*.csv)')            
            if file_name:
                logger.info(f'Файл сохранится как: {file_name}')        
                try:
                    df_to_save.to_csv(file_name, index=False, encoding='utf-8')
                    logger.info('Файл успешно сохранен.')                    
                except Exception as e: 
                    logger.error(f'Ошибка в процессе сохранения файла: {e}')                    
            else:
                logger.warning('Имя файла не выбрано.')
        else:
            logger.warning(f'Таблица {table_name} не найдена в области видимости.')
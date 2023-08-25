from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QTableView, QStackedWidget
from PyQt5.QtCore import Qt, QObject, pyqtSlot
import pandas as pd
from src.pandas_model import PandasModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TableManager(QObject):
    get_data_signal = pyqtSignal(str)
    get_data_returned_signal = pyqtSignal(pd.DataFrame)
    update_table_signal = pyqtSignal(str, pd.DataFrame)
    fill_table_signal = pyqtSignal(str)
    add_row_signal = pyqtSignal(str, pd.DataFrame)
    add_column_signal = pyqtSignal(str, str, object)
    delete_row_signal = pyqtSignal(int)
    delete_column_signal = pyqtSignal(int)
    fill_combo_boxes_signal = pyqtSignal(str, list, bool)
    get_column_data_signal = pyqtSignal(str, str)
    column_data_returned_signal = pyqtSignal(object)
    add_reaction_cumulative_func_signal = pyqtSignal(object, tuple, object, str, object)
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
    
    @pyqtSlot(str)
    def get_data(self, table_name):
        if table_name not in self.table_names:
            raise ValueError(f"Unknown table name: {table_name}")
        self.get_data_returned_signal.emit(self.data[table_name])
        return self.data[table_name]
    
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
            raise ValueError(f"Unknown table name: {table_name}")        

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
            raise ValueError(f"Unknown table name: {table_name}")

        if column_name in self.data[table_name].columns:
            raise ValueError(f"Column '{column_name}' already exists in table '{table_name}'")

        self.data[table_name][column_name] = column_data
        self.models[table_name] = PandasModel(self.data[table_name])
        self.tables[table_name].setModel(self.models[table_name])
        

    @pyqtSlot(str, pd.DataFrame)
    def add_row(self, table_name, row_data):
        if table_name not in self.table_names:
            raise ValueError(f"Unknown table name: {table_name}")

        self.data[table_name] = pd.concat([self.data[table_name], row_data], ignore_index=True)
        self.fill_table(table_name)

    @pyqtSlot(str, list, bool)
    def fill_combo_boxes(self, table_name, combo_boxes, block_signals=False):
        if table_name not in self.table_names:
            raise ValueError(f"Unknown table name: {table_name}")
        
        columns = self.data[table_name].columns
        logger.debug(f'fill_combo_boxes table_name: {table_name}, columns: {columns}')
        
        for combo_box in combo_boxes:
            if block_signals:
                combo_box.blockSignals(True)
            combo_box.clear()
            combo_box.addItems(columns)
            if block_signals:
                combo_box.blockSignals(False)

    @pyqtSlot(str, str)
    def get_column_data(self, table_name, column_name):
        logger.info(f'get_column_data table_name: {table_name} column_name: {column_name}')
        if table_name not in self.table_names:
            raise ValueError(f"Unknown table name: {table_name}")

        column_data = self.data[table_name][column_name]
        # Проверяем, являются ли данные числовыми
        if pd.to_numeric(column_data, errors='coerce').notna().all():
            self.column_data_returned_signal.emit(column_data)
            return column_data
        else:
            raise ValueError(f"Column {column_name} in table {table_name} contains non-numeric data")

    @pyqtSlot(object, tuple, object, str, object)
    def add_reaction_cumulative_func(self, best_params, best_combination, x_values, y_column, cumulative_func):
        for i, peak_type in enumerate(best_combination):
            a0 = best_params[3 * i]
            a1 = best_params[3 * i + 1]
            a2 = best_params[3 * i + 2]

            new_column_name = y_column + '_reaction_' + str(i)
            if peak_type == 'gauss':
                peak_func = self.math_operations.gaussian(x_values, a0, a1, a2)
            else:
                peak_func = self.math_operations.fraser_suzuki(x_values, a0, a1, a2, -1)
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
                                 'type':['gauss'],
                                 'coeff_1': [float(self.data['options']['coeff_1'].values)]
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



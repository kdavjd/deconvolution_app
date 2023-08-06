from PyQt5.QtWidgets import QTableView, QStackedWidget
import pandas as pd
from src.pandas_model import PandasModel

class TableManager:
    """Класс для управления функциональностью таблиц."""

    def __init__(self, viewer, math_operations, table_names, table_dict):
        """
        Инициализация класса.

        Параметры:
        -----------
        viewer : объект CSVViewer
            Объект CSVViewer для управления CSV данными.
        math_operations: объект MathOperations
            Объект для выполнения математических операций.
        table_names: list of str
            Список названий таблиц.
        """
        self.viewer = viewer
        self.math_operations = math_operations          
        self.table_names = table_names
        print(f"Inside TableManager init, table names: {self.table_names}")    
        self.data = {}
        self.models = {}
        self.tables = {}
        self.stacked_widget = QStackedWidget()
        # Словарь для соответствия имени таблицы и её индекса в stacked_widget
        self.table_indexes = {}
        
        for name in table_names:
            self.data[name] = table_dict[name]
            self.models[name] = PandasModel(self.data[name])
            self.tables[name] = QTableView()
            self.tables[name].setModel(self.models[name])
            self.stacked_widget.addWidget(self.tables[name])
            # Сохранение индекса таблицы в словаре
            self.table_indexes[name] = self.stacked_widget.count() - 1  
        
        print(f"Object ID at init: {id(self)} - table names: {self.table_names}")  
    
    def update_table_data(self, table_name, data):
        """
        Обновление данных в таблице.

        Параметры:
        -----------
        table_name: str
            Название таблицы для обновления.
        data: pandas DataFrame
            Новые данные для таблицы.
        """
        if table_name not in self.table_names:
            self.table_names.append(table_name)
            self.table_indexes[table_name] = self.stacked_widget.count()
            self.tables[table_name] = QTableView()
            self.stacked_widget.addWidget(self.tables[table_name])
        
        self.data[table_name] = data
        self.models[table_name] = PandasModel(self.data[table_name])
        self.tables[table_name].setModel(self.models[table_name])
    
    def fill_table(self, table_name): 
        """
        Заполнение таблицы данными.
        Используется для обновления представления таблиц.

        Параметры:
        -----------
        table_name: str
            Название таблицы для заполнения.
        """
        
        if table_name not in self.table_names:                      
            raise ValueError(f"Unknown table name: {table_name}")        
           
        self.models[table_name] = PandasModel(self.data[table_name])        
        self.tables[table_name].setModel(self.models[table_name])
        self.tables[table_name].reset()
        
        index = self.table_indexes[table_name]
        self.stacked_widget.setCurrentIndex(index)
        self.tables[table_name].update()     

    def add_row_to_table(self, table_name, row_data): 
        """        
        Используется для добавления строки данных в таблицу.

        Параметры:
        -----------
        table_name: str
            Название таблицы для добавления строки.
        row_data: pandas DataFrame
            Данные строки.
        """
        if table_name not in self.table_names:
            raise ValueError(f"Unknown table name: {table_name}")

        self.data[table_name] = pd.concat([self.data[table_name], row_data], ignore_index=True)
        self.fill_table(table_name)

    def delete_row(self, table_name, row_number):
        """
        Удаление строки из таблицы.
        Используется для управления данными в таблице.

        Параметры:
        -----------
        table_name: str
            Название таблицы для удаления строки.
        row_number: int
            Номер строки для удаления.
        """
        if table_name not in self.table_names:
            raise ValueError(f"Unknown table name: {table_name}")
        
        self.data[table_name] = self.data[table_name].drop(self.data[table_name].index[row_number])
        self.fill_table(table_name)

    def delete_column(self, table_name, column_number):
        """
        Удаление столбца из таблицы.
        Используется для управления структурой данных в таблице.

        Параметры:
        -----------
        table_name: str
            Название таблицы для удаления столбца.
        column_number: int
            Номер столбца для удаления.
        """
        if table_name not in self.table_names:
            raise ValueError(f"Unknown table name: {table_name}")
        
        column_name = self.data[table_name].columns[column_number]
        self.data[table_name] = self.data[table_name].drop(columns=[column_name])
        self.fill_table(table_name)

    def fill_combo_boxes(self, combo_box_x, combo_box_y):  # Изменено
        combo_box_x.clear()  # Изменено
        combo_box_y.clear()  # Изменено
        combo_box_x.addItems(self.viewer.df.columns)  # Изменено
        combo_box_y.addItems(self.viewer.df.columns)  # Изменено

    def get_column_data(self, column_name):
        column_data = self.viewer.df[column_name]
        # Проверяем, являются ли данные числовыми
        if pd.to_numeric(column_data, errors='coerce').notna().all():
            return column_data
        else:
            raise ValueError(f"Column {column_name} contains non-numeric data")

    def add_reaction_cummulative_func(self, best_params, best_combination, x_values, y_column, cummulative_func):
        for i, peak_type in enumerate(best_combination):
            a0 = best_params[3 * i]
            a1 = best_params[3 * i + 1]
            a2 = best_params[3 * i + 2]

            new_column_name = y_column + '_reaction_' + str(i)
            if peak_type == 'gauss':
                peak_func = self.math_operations.gaussian(x_values, a0, a1, a2)
            else:
                peak_func = self.math_operations.fraser_suzuki(x_values, a0, a1, a2, -1)
            self.viewer.df[new_column_name] = peak_func
            cummulative_func += peak_func

        new_column_name = y_column + '_cummulative'
        self.viewer.df[new_column_name] = cummulative_func
    
    def add_gaussian_to_table(self, height, center, width):  # Было: add_gaussian_to_table
        """        
        Используется для обновления данных о кривых и их визуализации.
        """
        row_data = pd.DataFrame({'Reaction': [f'Reaction_{self.gaussian_data.shape[0] + 1}'], 
                                 'Height': [height],
                                 'Center': [center],
                                 'Width': [width],
                                 'Type':['gauss']
                                 })
        self.gaussian_data = pd.concat([self.gaussian_data, row_data], ignore_index=True)
        self.models['gauss'] = PandasModel(self.gaussian_data)
        self.tables['gauss'].setModel(self.gaussian_model)

    def delete_row(self, row_number):  # Было: deleteRow
        """
        Удаление строки из активного DataFrame.
        Используется для управления данными в активной таблице.
        """
        if self.stacked_widget.currentIndex() == 0:
            self.viewer.df = self.viewer.df.drop(self.viewer.df.index[row_number])
            self.csv_model = PandasModel(self.viewer.df)
            self.csv_table.setModel(self.csv_model)
        elif self.stacked_widget.currentIndex() == 1:
            self.gaussian_data = self.gaussian_data.drop(self.gaussian_data.index[row_number])
            self.gaussian_model = PandasModel(self.gaussian_data)
            self.gaussian_table.setModel(self.gaussian_model)

    def delete_column(self, column_number):  # Было: deleteColumn
        """
        Удаление столбца из активного DataFrame.
        Используется для управления структурой данных в активной таблице.
        """
        column_name = None
        if self.stacked_widget.currentIndex() == 0:
            column_name = self.viewer.df.columns[column_number]
            self.viewer.df = self.viewer.df.drop(columns=[column_name])
            self.csv_model = PandasModel(self.viewer.df)
            self.csv_table.setModel(self.csv_model)
        elif self.stacked_widget.currentIndex() == 1:
            column_name = self.gaussian_data.columns[column_number]
            self.gaussian_data = self.gaussian_data.drop(columns=[column_name])
            self.gaussian_model = PandasModel(self.gaussian_data)
            self.gaussian_table.setModel(self.gaussian_model)


from PyQt5.QtWidgets import QTableView, QComboBox, QStackedWidget
import pandas as pd
import numpy as np
from pandas_model import PandasModel

class TableManager:
    """Класс для управления функциональностью таблиц."""

    def __init__(self, viewer, math_operations):
        """
        Инициализация класса.

        Параметры:
        -----------
        viewer : объект CSVViewer
            Объект CSVViewer для управления CSV данными.
        math_operations: объект MathOperations
            Объект для выполнения математических операций.
        """
        self.viewer = viewer
        self.math_operations = math_operations
        self.gaussian_data = pd.DataFrame(columns=['Reaction', 'Height', 'Center', 'Width'])
        self.gaussian_model = PandasModel(self.gaussian_data)
        self.gaussian_table = QTableView()
        self.gaussian_table.setModel(self.gaussian_model)
        self.csv_table = QTableView()
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.csv_table)
        self.stacked_widget.addWidget(self.gaussian_table)

    def fill_main_table(self):  # Было: fillMainTable
        """
        Заполнение основной таблицы данными из объекта viewer.
        Используется для обновления представления основной таблицы.
        """
        self.csv_model = PandasModel(self.viewer.df)
        self.csv_table.setModel(self.csv_model)
        
    def fill_gauss_table(self):  # Было: fillGaussTable
        """
        Заполнение таблицы данными о гауссовых кривых.
        Используется для обновления представления таблицы гауссовых кривых.
        """
        self.gaussian_model = PandasModel(self.gaussian_data)
        self.gaussian_table.setModel(self.gaussian_model)

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
    
    def init_params(self):
        init_params = []
        for _, row in self.gaussian_data.iterrows():
            init_params.extend([row['Height'], row['Center'], row['Width']])
        return init_params

    def update_gaussian_data(self, best_params, best_combination):
        for i, peak_type in enumerate(best_combination):
            a0 = best_params[3*i]
            a1 = best_params[3*i+1]
            a2 = best_params[3*i+2]
            self.gaussian_data.at[i, 'Height'] = a0
            self.gaussian_data.at[i, 'Center'] = a1
            self.gaussian_data.at[i, 'Width'] = a2
            self.gaussian_data.at[i, 'Type'] = peak_type

    def compute_peaks(self, x_column, y_column):  # Было: computePeaks
        """
        Вычисление и обновление данных о пиках.
        Используется для анализа данных и их визуализации.
        """
        init_params = self.init_params()
        x_values = self.get_column_data(x_column)
        y_values = self.get_column_data(y_column)

        best_params, best_combination, best_rmse = self.math_operations.compute_best_peaks(x_values, y_values, init_params)
        cummulative_func = np.zeros(len(x_values))

        self.update_gaussian_data(best_params, best_combination)
        self.add_reaction_cummulative_func(best_params, best_combination, x_values, y_column, cummulative_func)
        self.fill_gauss_table() # Было: fillGaussTable
        self.fill_main_table() # Было: fillMainTable
    
    def add_diff(self, x_column, y_column, combo_box_x, combo_box_y):  # Изменено
        dy_dx = self.math_operations.compute_derivative(self.viewer.df[x_column], self.viewer.df[y_column])
        new_column_name = y_column + '_diff'
        self.viewer.df[new_column_name] = dy_dx
        self.fill_main_table()
        self.fill_combo_boxes(combo_box_x, combo_box_y)  # Изменено
        combo_box_y.setCurrentText(new_column_name)  # Изменено
    
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
        self.gaussian_model = PandasModel(self.gaussian_data)
        self.gaussian_table.setModel(self.gaussian_model)

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


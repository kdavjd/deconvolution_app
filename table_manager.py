from PyQt5.QtWidgets import QTableView, QComboBox, QStackedWidget
import pandas as pd
import numpy as np
from pandas_model import PandasModel

class TableManager:
    """Класс для управления функциональностью таблиц."""

    def __init__(self, viewer):
        """
        Инициализация класса.

        Параметры:
        -----------
        viewer : объект CSVViewer
            Объект CSVViewer для управления CSV данными.
        """
        # Сохраняем объект CSVViewer для управления CSV данными
        self.viewer = viewer

        # Создаем DataFrame для хранения данных о гауссовых кривых
        self.gaussian_data = pd.DataFrame(columns=['Reaction', 'Height', 'Center', 'Width'])

        # Создаем модель данных на основе DataFrame
        self.gaussian_model = PandasModel(self.gaussian_data)

        # Создаем виджет для отображения данных модели
        self.gaussian_table = QTableView()
        self.gaussian_table.setModel(self.gaussian_model)

        # Создаем таблицу для отображения данных CSV
        self.csv_table = QTableView()

        # Создаем виджет, который может переключаться между разными виджетами (в нашем случае между таблицами)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.csv_table)
        self.stacked_widget.addWidget(self.gaussian_table)

    def fillMainTable(self):
        """
        Заполнение таблицы данными.

        Использует данные из объекта viewer, чтобы заполнить таблицу csv.
        """
        # Создаем модель данных на основе данных CSV
        self.csv_model = PandasModel(self.viewer.df)

        # Устанавливаем модель данных для таблицы CSV
        self.csv_table.setModel(self.csv_model)
        
    def fillGaussTable(self):
        """
        Заполнение таблицы данными.

        Использует данные из объекта viewer, чтобы заполнить таблицу csv.
        """
        # Создаем модель данных на основе данных CSV
        self.gaussian_model = PandasModel(self.gaussian_data)

        # Устанавливаем модель данных для таблицы CSV
        self.gaussian_table.setModel(self.gaussian_model)

    def fillComboBoxes(self, comboBoxX, comboBoxY):
        """
        Заполнение комбобоксов данными.

        Использует столбцы данных из объекта viewer, чтобы заполнить комбобоксы.

        Параметры:
        -----------
        comboBoxX : QComboBox
            Комбобокс для выбора столбца X.
        comboBoxY : QComboBox
            Комбобокс для выбора столбца Y.
        """
        # Очищаем комбобоксы
        comboBoxX.clear()
        comboBoxY.clear()

        # Заполняем комбобоксы именами столбцов из данных CSV
        comboBoxX.addItems(self.viewer.df.columns)
        comboBoxY.addItems(self.viewer.df.columns)

    def get_column_data(self, column_name):
        column_data = self.viewer.df[column_name]
        # Проверяем, являются ли данные числовыми
        if pd.to_numeric(column_data, errors='coerce').notna().all():
            return column_data
        else:
            raise ValueError(f"Column {column_name} contains non-numeric data")

    def add_reaction_cummulative_func(self, best_params, best_combination, x_values, y_column, cummulative_func, math_operations):
        for i, peak_type in enumerate(best_combination):
            a0 = best_params[3 * i]
            a1 = best_params[3 * i + 1]
            a2 = best_params[3 * i + 2]

            new_column_name = y_column + '_reaction_' + str(i)
            if peak_type == 'gauss':
                peak_func = math_operations.gaussian(x_values, a0, a1, a2)
            else:
                peak_func = math_operations.fraser_suzuki(x_values, a0, a1, a2, -1)
            self.viewer.df[new_column_name] = peak_func
            cummulative_func += peak_func

        new_column_name = y_column + '_cummulative'
        self.viewer.df[new_column_name] = cummulative_func
    
    def add_gaussian_to_table(self, height, center, width):
        """
        Добавление гауссовской функции в таблицу.

        Создает новую строку данных о гауссовой кривой и добавляет ее в таблицу.

        Параметры:
        -----------
        height : float
            Высота гауссовой кривой.
        center : float
            Центр гауссовой кривой.
        width : float
            Ширина гауссовой кривой.
        """
        # Создаем новую строку данных
        row_data = pd.DataFrame({'Reaction': [f'Reaction_{self.gaussian_data.shape[0] + 1}'], 
                                 'Height': [height],
                                 'Center': [center],
                                 'Width': [width],
                                 'Type':['gauss']
                                 })
        
        # Добавляем новую строку в данные
        self.gaussian_data = pd.concat([self.gaussian_data, row_data], ignore_index=True)

        # Обновляем модель данных
        self.gaussian_model = PandasModel(self.gaussian_data)
        self.gaussian_table.setModel(self.gaussian_model)

    def deleteRow(self, row_number):
        """Удаление строки из активного DataFrame."""
        if self.stacked_widget.currentIndex() == 0:  # Если активна таблица CSV
            self.viewer.df = self.viewer.df.drop(self.viewer.df.index[row_number])
            self.csv_model = PandasModel(self.viewer.df)
            self.csv_table.setModel(self.csv_model)
        elif self.stacked_widget.currentIndex() == 1:  # Если активна таблица Gaus
            self.gaussian_data = self.gaussian_data.drop(self.gaussian_data.index[row_number])
            self.gaussian_model = PandasModel(self.gaussian_data)
            self.gaussian_table.setModel(self.gaussian_model)

    def deleteColumn(self, column_number):
        """Удаление столбца из активного DataFrame."""
        column_name = None
        if self.stacked_widget.currentIndex() == 0:  # Если активна таблица CSV
            column_name = self.viewer.df.columns[column_number]
            self.viewer.df = self.viewer.df.drop(columns=[column_name])
            self.csv_model = PandasModel(self.viewer.df)
            self.csv_table.setModel(self.csv_model)
        elif self.stacked_widget.currentIndex() == 1:  # Если активна таблица Gaus
            column_name = self.gaussian_data.columns[column_number]
            self.gaussian_data = self.gaussian_data.drop(columns=[column_name])
            self.gaussian_model = PandasModel(self.gaussian_data)
            self.gaussian_table.setModel(self.gaussian_model)


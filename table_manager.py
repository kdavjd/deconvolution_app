from PyQt5.QtWidgets import QTableView, QComboBox, QStackedWidget
import pandas as pd
import numpy as np
from pandas_model import PandasModel

class TableManager:
    """Класс для управления функциональностью таблиц."""
    
    def __init__(self, viewer):
        """Инициализация класса."""
        self.viewer = viewer
        self.gaussian_data = pd.DataFrame(columns=['Reaction', 'Height', 'Center', 'Width'])
        self.gaussian_model = PandasModel(self.gaussian_data)
        self.gaussian_table = QTableView()
        self.gaussian_table.setModel(self.gaussian_model)

        self.csv_table = QTableView()

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.csv_table)
        self.stacked_widget.addWidget(self.gaussian_table)

    def fillTable(self):
        """Заполнение таблицы данными."""
        self.csv_model = PandasModel(self.viewer.df)
        self.csv_table.setModel(self.csv_model)

    def fillComboBoxes(self, comboBoxX, comboBoxY):
        """Заполнение комбобоксов данными."""
        comboBoxX.clear()
        comboBoxY.clear()
        comboBoxX.addItems(self.viewer.df.columns)
        comboBoxY.addItems(self.viewer.df.columns)

    def add_gaussian_to_table(self, height, center, width):
        """Добавление гауссовской функции в таблицу."""
        row_data = pd.DataFrame({'Reaction': [f'Reaction_{self.gaussian_data.shape[0] + 1}'], 
                                'Height': [height], 'Center': [center], 'Width': [width]})
        self.gaussian_data = pd.concat([self.gaussian_data, row_data], ignore_index=True)
        self.gaussian_model = PandasModel(self.gaussian_data)
        self.gaussian_table.setModel(self.gaussian_model)

    def deleteColumn(self, comboBoxX, comboBoxY, currentIndex):
        """Удаление колонки из таблицы."""
        if currentIndex == 0:
            self.viewer.df.drop([comboBoxX.currentText()], axis=1, inplace=True)
            self.fillTable()
            self.fillComboBoxes(comboBoxX, comboBoxY)
        elif currentIndex == 1:
            if self.gaussian_table.currentIndex().row() >= 0:
                self.gaussian_data.drop(self.gaussian_table.currentIndex().row(), inplace=True)
                self.gaussian_data.reset_index(drop=True, inplace=True)
                self.gaussian_model = PandasModel(self.gaussian_data)
                self.gaussian_table.setModel(self.gaussian_model)

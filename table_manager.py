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

    def fillTable(self):
        """
        Заполнение таблицы данными.

        Использует данные из объекта viewer, чтобы заполнить таблицу csv.
        """
        # Создаем модель данных на основе данных CSV
        self.csv_model = PandasModel(self.viewer.df)

        # Устанавливаем модель данных для таблицы CSV
        self.csv_table.setModel(self.csv_model)

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
                                 'Height': [height], 'Center': [center], 'Width': [width]})
        
        # Добавляем новую строку в данные
        self.gaussian_data = pd.concat([self.gaussian_data, row_data], ignore_index=True)

        # Обновляем модель данных
        self.gaussian_model = PandasModel(self.gaussian_data)
        self.gaussian_table.setModel(self.gaussian_model)

    def deleteColumn(self, comboBoxX, comboBoxY, currentIndex):
        """
        Удаление колонки из таблицы.

        Удаляет выбранный столбец из данных CSV или выбранную строку из данных о гауссовых кривых.

        Параметры:
        -----------
        comboBoxX : QComboBox
            Комбобокс для выбора столбца X.
        comboBoxY : QComboBox
            Комбобокс для выбора столбца Y.
        currentIndex : int
            Индекс текущего выбранного виджета в stacked_widget.
        """
        # Если текущий выбранный виджет - это таблица CSV
        if currentIndex == 0:
            # Удаляем выбранный столбец из данных
            self.viewer.df.drop([comboBoxX.currentText()], axis=1, inplace=True)

            # Обновляем таблицу и комбобоксы
            self.fillTable()
            self.fillComboBoxes(comboBoxX, comboBoxY)
        
        # Если текущий выбранный виджет - это таблица с гауссовыми кривыми
        elif currentIndex == 1:
            # Проверяем, выбрана ли строка в таблице
            if self.gaussian_table.currentIndex().row() >= 0:
                # Удаляем выбранную строку из данных
                self.gaussian_data.drop(self.gaussian_table.currentIndex().row(), inplace=True)

                # Обновляем индексы в данных
                self.gaussian_data.reset_index(drop=True, inplace=True)

                # Обновляем модель данных
                self.gaussian_model = PandasModel(self.gaussian_data)
                self.gaussian_table.setModel(self.gaussian_model)


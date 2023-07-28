# csv_viewer.py
from PyQt5.QtWidgets import QFileDialog
import os
import pandas as pd
import chardet
import numpy as np

class CSVViewer(): # Класс отвечает за обработку CSV файлов.
    def __init__(self):
        self.df = pd.DataFrame() # Создаем пустой DataFrame для хранения данных.

    def getCSV(self):
        # Эта функция загружает CSV файл, выбранный пользователем в главном окне приложения.        
        self.fileName, _ = QFileDialog.getOpenFileName(None, 'Open CSV', os.getenv('HOME'), 'CSV(*.csv)')
        if self.fileName:
            self.loadCSV()

    def loadCSV(self):
        # Эта функция считывает данные из CSV файла и сохраняет их в DataFrame.
        # Определение кодировки файла
        with open(self.fileName, 'rb') as f:
            result = chardet.detect(f.read())
        file_encoding = result['encoding']

        # Считывание данных из CSV файла
        self.df = pd.read_csv(
            self.fileName,
            encoding=file_encoding,
        )
    
    def add_diff_column(self, x_col_name, y_col_name):
        """
        Функция добавляет новый столбец в DataFrame. Значения нового столбца это отношение np.gradient() dy/dx 
        от переменных, выбранных для отрисовки графика x и y соответственно. Имя нового столбца образуется из 
        названия столбца под переменной y и приставкой _diff в конце.
        
        Параметры:
        x_col_name : str
            Название столбца DataFrame, который используется как ось x для графика.
        y_col_name : str
            Название столбца DataFrame, который используется как ось y для графика.
        """
        if x_col_name == '' or y_col_name == '':
            print('Please, select columns for X and Y before adding a diff column.')
            return

        # Рассчитываем производную y по x с помощью np.gradient()
        y_values = self.df[y_col_name]
        x_values = self.df[x_col_name]
        dy_dx = np.gradient(y_values, x_values) * -1
    
        # Создаем новый столбец с производной и добавляем его в DataFrame
        new_column_name = y_col_name + '_diff'
        self.df[new_column_name] = dy_dx

    def plotGraph(self, x_column, y_column, figure, canvas):
        x = self.df[x_column]
        y = self.df[y_column]

        # Очищаем текущий график
        figure.clear()

        # Создаем новый график
        ax = figure.add_subplot(111)

        # Отрисовываем график
        ax.plot(x, y, '*-')

        # Обновляем область отображения графика
        canvas.draw()

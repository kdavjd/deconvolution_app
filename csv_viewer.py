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

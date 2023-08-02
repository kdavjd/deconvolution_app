from PyQt5.QtWidgets import QFileDialog
import os
import pandas as pd
import chardet

class CSVViewer(): # Класс отвечает за обработку CSV файлов.
    def __init__(self):
        self.df = pd.DataFrame() # Создаем пустой DataFrame для хранения данных.

    def initialize(self, tableManager, uiInitializer):
        # Устанавливаем ссылки на tableManager и uiInitializer
        self.tableManager = tableManager
        self.uiInitializer = uiInitializer

    def getCSV(self):
        # Эта функция загружает CSV файл, выбранный пользователем в главном окне приложения.        
        self.fileName, _ = QFileDialog.getOpenFileName(None, 'Open CSV', os.getenv('HOME'), 'CSV(*.csv)')
        if self.fileName:
            self.loadCSV()
            self.tableManager.fillComboBoxes(self.uiInitializer.comboBoxX, self.uiInitializer.comboBoxY)
            self.tableManager.fillTable()

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
        
    def exportCSV(self):
        # Эта функция экспортирует текущий DataFrame в файл CSV.
        self.fileName, _ = QFileDialog.getSaveFileName(None, 'Save CSV', os.getenv('HOME'), 'CSV(*.csv)')
        if self.fileName:
            self.df.to_csv(self.fileName, index=False, encoding='utf-8')
   

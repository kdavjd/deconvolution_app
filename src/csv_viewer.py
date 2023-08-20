from PyQt5.QtWidgets import QFileDialog
import os
import pandas as pd
import chardet

class CSVViewer: # Класс отвечает за обработку CSV файлов.
    
    def __init__(self, table_dict):
        self.df = pd.DataFrame()
        self.table_dict = table_dict
        self.file_name = None
        
    def initialize(self, table_manager, ui_initializer): 
        # Устанавливаем ссылки на table_manager и ui_initializer
        self.table_manager = table_manager 
        self.ui_initializer = ui_initializer 

    def get_csv(self):
        # Эта функция загружает CSV файл, выбранный пользователем в главном окне приложения.        
        self.file_path, _ = QFileDialog.getOpenFileName(None, 'Open CSV', os.getenv('HOME'), 'CSV(*.csv)')
        if self.file_path: 
            self.load_csv()
            
            file_name_with_extension = os.path.basename(self.file_path)
            self.file_name, _ = os.path.splitext(file_name_with_extension)
            self.file_name = self.file_name.strip()
           

    def load_csv(self): # Было: loadCSV
        # Эта функция считывает данные из CSV файла и сохраняет их в DataFrame.
        # Определение кодировки файла
        with open(self.file_path, 'rb') as f: 
            result = chardet.detect(f.read())
        file_encoding = result['encoding']

        # Считывание данных из CSV файла
        self.df = pd.read_csv(
            self.file_path, 
            encoding=file_encoding,
        ) 
        
    def export_csv(self): # Было: exportCSV
        # Эта функция экспортирует текущий DataFrame в файл CSV.
        self.file_name, _ = QFileDialog.getSaveFileName(None, 'Save CSV', os.getenv('HOME'), 'CSV(*.csv)') 
        if self.file_name: 
            self.df.to_csv(self.file_name, index=False, encoding='utf-8') #
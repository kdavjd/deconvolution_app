from PyQt5.QtWidgets import QFileDialog
import os
import pandas as pd
import chardet

class CSVViewer: # Класс отвечает за обработку CSV файлов.
    
    def __init__(self, table_dict):
        self.df = pd.DataFrame() # Создаем пустой DataFrame для хранения данных.
        self.table_dict = table_dict
        self.file_name = None
        
    def initialize(self, table_manager, ui_initializer): # Было: tableManager, uiInitializer
        # Устанавливаем ссылки на table_manager и ui_initializer
        self.table_manager = table_manager # Было: tableManager
        self.ui_initializer = ui_initializer # Было: uiInitializer

    def get_csv(self):
        # Эта функция загружает CSV файл, выбранный пользователем в главном окне приложения.        
        self.file_path, _ = QFileDialog.getOpenFileName(None, 'Open CSV', os.getenv('HOME'), 'CSV(*.csv)')
        if self.file_path: 
            self.load_csv() 
            self.table_manager.fill_combo_boxes(self.ui_initializer.combo_box_x, self.ui_initializer.combo_box_y)
            file_name_with_extension = os.path.basename(self.file_path)
            self.file_name, _ = os.path.splitext(file_name_with_extension)
            self.file_name = self.file_name.strip()
            
        

    def load_csv(self): # Было: loadCSV
        # Эта функция считывает данные из CSV файла и сохраняет их в DataFrame.
        # Определение кодировки файла
        with open(self.file_path, 'rb') as f: # Было: fileName
            result = chardet.detect(f.read())
        file_encoding = result['encoding']

        # Считывание данных из CSV файла
        self.df = pd.read_csv(
            self.file_path, # Было: fileName
            encoding=file_encoding,
        )
        
             
        
        
    def export_csv(self): # Было: exportCSV
        # Эта функция экспортирует текущий DataFrame в файл CSV.
        self.file_name, _ = QFileDialog.getSaveFileName(None, 'Save CSV', os.getenv('HOME'), 'CSV(*.csv)') # Было: fileName
        if self.file_name: # Было: fileName
            self.df.to_csv(self.file_name, index=False, encoding='utf-8') #
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout, QLabel, QLineEdit, QGroupBox
from PyQt5.QtCore import QObject, pyqtSignal
from src.sub_handlers.graph_handler import GraphHandler
from src.sub_handlers.data_handler import DataHandler
from src.sub_handlers.ui_handler import UIHandler
import numpy as np
from itertools import product

from src.logger_config import logger


class EventHandler(QObject):
    update_console_signal = pyqtSignal(str)
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.graph_handler = GraphHandler(main_app)
        self.data_handler = DataHandler(main_app)
        self.ui_handler = UIHandler(main_app) 
    
    # Создание и отображение диалогового окна для выбора типов пиков и их ограничений. 
    def fetch_peak_type_and_bounds(self):              
        dialog = self.create_dialog()
        reactions = self.data_handler.retrieve_table_data('gauss')['reaction']
        checkboxes, coeffs_bounds_inputs, peaks_params_inputs = self.create_reaction_groups(dialog, reactions)
        
        if dialog.exec_():
            selected, combinations, coeffs_bounds, peaks_params = self.extract_input_values(reactions, checkboxes, coeffs_bounds_inputs, peaks_params_inputs)
            return selected, combinations, coeffs_bounds, peaks_params
        else:
            return None, None, None, None
    
    # Создание основного диалогового окна.    
    def create_dialog(self):        
        dialog = QDialog()
        dialog.setWindowTitle("Выбор типов пиков и ограничений")
        dialog.setLayout(QHBoxLayout())
        dialog.layout().setSpacing(0)
        return dialog
    
    # Создание групповых полей для каждой реакции.
    def create_reaction_groups(self, dialog, reactions):        
        checkboxes = {}
        coeffs_bounds_inputs = {}
        peaks_params_inputs = {}
        
        for reaction in reactions:
            group_box, layout = self.create_group_box(reaction)
            checkboxes[reaction], coeffs_bounds_inputs[reaction], peaks_params_inputs[reaction] = self.create_reaction_controls(layout, reaction)
            
            dialog.layout().addWidget(group_box)
            dialog.layout().setStretchFactor(group_box, 1)
        
        btn = QPushButton("Применить")
        btn.clicked.connect(dialog.accept)
        dialog.layout().addWidget(btn)
        
        return checkboxes, coeffs_bounds_inputs, peaks_params_inputs
    
    # Создание группового поля для конкретной реакции.
    def create_group_box(self, reaction):
        group_box = QGroupBox(reaction)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        group_box.setContentsMargins(10, 10, 10, 10)
        group_box.setLayout(layout)
        return group_box, layout

    # Добавление элементов управления (флажки, поля ввода) внутри группового поля реакции.
    def create_reaction_controls(self, layout, reaction):
        gauss_data = self.data_handler.retrieve_table_data('gauss')
        reaction_row = gauss_data[gauss_data['reaction'] == reaction]

        checkboxes = self.create_checkboxes(layout)
        coeffs_bounds_inputs = self.create_coeffs_bounds_inputs(layout, reaction_row)
        peaks_params_inputs = self.create_peaks_params_inputs(layout, reaction_row)
        
        return checkboxes, coeffs_bounds_inputs, peaks_params_inputs

    # Создание флажков для выбора типа пика.
    def create_checkboxes(self, layout):
        checkboxes = {}
        for peak_type in ['gauss', 'fraser', 'ads']:
            checkbox = QCheckBox(peak_type)
            checkbox.setChecked(True)
            layout.addWidget(checkbox)
            checkboxes[peak_type] = checkbox
        return checkboxes

    # Создание полей ввода для задания ограничений коэффициентов.
    def create_coeffs_bounds_inputs(self, layout, reaction_row):
        constraint_to_column = {
            'a_bottom_constraint': 'coeff_a', 
            'a_top_constraint': 'coeff_a', 
            's1_bottom_constraint': 'coeff_s1', 
            's1_top_constraint': 'coeff_s1', 
            's2_bottom_constraint': 'coeff_s2', 
            's2_top_constraint': 'coeff_s2'
        }
        coeffs_bounds_inputs = {}
        
        for peak_type in ['gauss', 'fraser', 'ads']:
            coeffs_bounds_inputs[peak_type] = self.create_peak_type_bounds(peak_type, layout, reaction_row, constraint_to_column)
        return coeffs_bounds_inputs

    # Создание полей ввода ограничений для конкретного типа пика.
    def create_peak_type_bounds(self, peak_type, layout, reaction_row, constraint_to_column):
        bounds = {}
        
        if peak_type == 'fraser':
            constraints = [('a_bottom_constraint', 'a_top_constraint')]
        elif peak_type == 'ads':
            constraints = [('s1_bottom_constraint', 's1_top_constraint'), ('s2_bottom_constraint', 's2_top_constraint')]
        else:
            constraints = []
            
        for constraint_pair in constraints:
            lower_constraint, upper_constraint = constraint_pair
            h_layout = QHBoxLayout()
            label = QLabel(f"{lower_constraint.split('_')[0]}_coeff_bounds")
            layout.addWidget(label)
            
            base_value = float(reaction_row[constraint_to_column[lower_constraint]].values[0]) if not reaction_row.empty else 0.0
            initial_lower_value = str(base_value * 0.8)
            initial_upper_value = str(base_value * 1.2)
            
            for constraint in constraint_pair:
                if "bottom" in constraint:
                    input_field = QLineEdit(initial_lower_value)
                else:
                    input_field = QLineEdit(initial_upper_value)
                h_layout.addWidget(input_field)
                bounds[constraint] = input_field
                
            layout.addLayout(h_layout)
        return bounds


    # Создание полей ввода для параметров пиков.
    def create_peaks_params_inputs(self, layout, reaction_row):
        peaks_params_inputs = {}
        for param in ['height', 'center', 'width']:
            param_layout = QVBoxLayout()
            label = QLabel(f"{param}_bounds")
            param_layout.addWidget(label)
            
            h_layout = QHBoxLayout()
            value = float(reaction_row[param].values[0])
            initial_lower_value = np.round(value * 0.8, 3) if not reaction_row.empty else "0.0"
            initial_upper_value = np.round(value * 1.2, 3) if not reaction_row.empty else "0.0"
            
            input_lower = QLineEdit(str(initial_lower_value))
            input_upper = QLineEdit(str(initial_upper_value))
            
            h_layout.addWidget(input_lower)
            h_layout.addWidget(input_upper)
            
            param_layout.addLayout(h_layout)
            layout.addLayout(param_layout)
            peaks_params_inputs[param] = (input_lower, input_upper)
        return peaks_params_inputs

    # Извлечение данных из элементов управления и формирование результатов выбора.
    def extract_input_values(self, reactions, checkboxes, coeffs_bounds_inputs, peaks_params_inputs):
        selected = {}
        coeffs_bounds = {}
        peaks_bounds = {}
        for reaction in reactions:
            # Создаем список типов пиков, отмеченных пользователем в пользовательском интерфейсе.
            # Для каждой реакции, мы итерируемся через ее чекбоксы и проверяем, отмечен ли чекбокс.
            # Если отмечен, тип пика добавляется в список.
            selected[reaction] = [peak_type for peak_type, checkbox in checkboxes[reaction].items() if checkbox.isChecked()]
            # Извлекаем ограничения на коэффициенты, введенные пользователем для каждой реакции и типа пика.
            # Для каждой реакции и каждого типа пика, мы итерируемся через входные поля ограничений и
            # сохраняем их значения как числа с плавающей точкой.
            coeffs_bounds[reaction] = {
                peak_type: {constraint: float(input_field.text()) for constraint, input_field in constraints.items()
                            } for peak_type, constraints in coeffs_bounds_inputs[reaction].items()}
            # Извлекаем параметры пиков, такие как нижние и верхние границы, введенные пользователем.
            # Для каждой реакции, мы итерируемся через входные поля параметров пиков и
            # сохраняем их значения как кортежи чисел с плавающей точкой.
            peaks_bounds[reaction] = {
                param: (float(input_lower.text()), float(input_upper.text())) 
                for param, (input_lower, input_upper) in peaks_params_inputs[reaction].items()}
        # Создаем список из типов пиков, выбранных пользователем для каждой реакции.          
        selected_peak_types = [selected[reaction] for reaction in reactions]
        # Генерируем все возможные комбинации типов пиков, выбранных пользователем.
        combinations = list(product(*selected_peak_types))
        
        logger.debug(f'selected combinations: {selected}')
        logger.debug(f'producted combinations: {combinations}')
        logger.debug(f'producted bounds: {coeffs_bounds}')
        logger.debug(f'peaks params bounds: {peaks_bounds}')
        
        return selected, combinations, coeffs_bounds, peaks_bounds

    def extract_bounds_selected_combinations(self, selected_combinations, coeffs_bounds):
        # Инициализируем список, который будет содержать результаты (границы коэффициентов для различных функций)
        result = []

        # Словарь для определения ключей границ коэффициентов для различных функций. 
        # Ключ словаря - это название функции, значение - список кортежей с ключами для нижней и верхней границы.
        bounds_keys = {
            'fraser': [('a_bottom_constraint', 'a_top_constraint')],
            'ads': [('s1_bottom_constraint', 's1_top_constraint'),
                    ('s2_bottom_constraint', 's2_top_constraint')]
        }
        # Начинаем обход всех реакций в selected_combinations 
        for reaction, functions in selected_combinations.items():
            # Обходим все функции, связанные с текущей реакцией
            for func in functions:
                # Проверяем, присутствует ли текущая функция в нашем словаре bounds_keys (то есть нам нужны ее границы)
                if func in bounds_keys:  
                    # Если функция присутствует, обходим все соответствующие ей ключи границ
                    for bottom_key, top_key in bounds_keys[func]:
                        # Извлекаем границы для текущей функции из coeffs_bounds
                        bounds = coeffs_bounds[reaction][func]
                        # Добавляем извлеченные границы в результат
                        result.append((bounds[bottom_key], bounds[top_key]))
                        
        logger.debug(f'extracted_bounds: {result}')
        # Возвращаем итоговый список с границами
        return result
    
    def extract_peaks_bounds(self, bounds_dict):
        lower_bounds = []
        upper_bounds = []
        
        for reaction, params in bounds_dict.items():
            for param, bounds in params.items():
                lower, upper = bounds
                lower_bounds.append(lower)
                upper_bounds.append(upper)
        
        return lower_bounds, upper_bounds
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
   
    def get_selected_peak_types(self):
        dialog = QDialog()
        dialog.setWindowTitle("Выбор типов пиков и ограничений")

        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        
        gauss_data = self.data_handler.retrieve_table_data('gauss')
        reactions = gauss_data['reaction']
        checkboxes = {}
        bounds_inputs = {}
        other_bounds_inputs = {} 
        constraint_to_column = {
            'a_bottom_constraint': 'coeff_a', 
            'a_top_constraint': 'coeff_a', 
            's1_bottom_constraint': 'coeff_s1', 
            's1_top_constraint': 'coeff_s1', 
            's2_bottom_constraint': 'coeff_s2', 
            's2_top_constraint': 'coeff_s2'
        }
        for reaction in reactions:
            # Создаём группу для каждой реакции
            group_box = QGroupBox(reaction)            
            layout = QVBoxLayout()
            layout.setContentsMargins(10, 10, 10, 10)  # Установка отступов на ноль
            group_box.setContentsMargins(10, 10, 10, 10)  # Установка отступов на ноль
            
            checkboxes[reaction] = {}
            bounds_inputs[reaction] = {}

            # Верхняя область с чекбоксами
            for peak_type in ['gauss', 'fraser', 'ads']:
                checkbox = QCheckBox(peak_type)
                checkbox.setChecked(True)
                layout.addWidget(checkbox)
                checkboxes[reaction][peak_type] = checkbox

            # Находим строку для текущей реакции в gauss_data
            reaction_row = gauss_data[gauss_data['reaction'] == reaction]

            for peak_type in ['gauss', 'fraser', 'ads']:
                if peak_type == 'fraser':
                    constraints = [('a_bottom_constraint', 'a_top_constraint')]
                elif peak_type == 'ads':
                    constraints = [('s1_bottom_constraint', 's1_top_constraint'), ('s2_bottom_constraint', 's2_top_constraint')]
                else:
                    constraints = []

                bounds_inputs[reaction][peak_type] = {}

                for constraint_pair in constraints:
                    lower_constraint, upper_constraint = constraint_pair

                    # создаем новый горизонтальный layout для двух полей ввода
                    h_layout = QHBoxLayout()
                    label = QLabel(f"{lower_constraint.split('_')[0]}_coeff_bounds")
                    layout.addWidget(label)

                    for constraint in constraint_pair:
                        coeff_column = constraint_to_column[constraint]  
                        initial_value = str(reaction_row[coeff_column].values[0]) if not reaction_row.empty else "0.0"
                        input_field = QLineEdit(initial_value)
                        h_layout.addWidget(input_field)
                        bounds_inputs[reaction][peak_type][constraint] = input_field

                    layout.addLayout(h_layout)
                    
            other_bounds_inputs[reaction] = {}

            # Находим строку для текущей реакции в gauss_data
            reaction_row = gauss_data[gauss_data['reaction'] == reaction]

            # Для каждого параметра ('height', 'center', 'width')
            for param in ['height', 'center', 'width']:
                param_layout = QVBoxLayout()  # новый вертикальный layout для каждого параметра
                label = QLabel(f"{param}_bounds")
                param_layout.addWidget(label)

                h_layout = QHBoxLayout()  # новый горизонтальный layout для полей ввода

                # Здесь мы извлекаем соответствующие значения из таблицы
                initial_lower_value = str(np.round(reaction_row[param].values[0]*0.8, 3)) if not reaction_row.empty else "0.0"
                initial_upper_value = str(np.round(reaction_row[param].values[0]*1.2, 3)) if not reaction_row.empty else "0.0"

                input_lower = QLineEdit(initial_lower_value)  # поле для нижней границы
                input_upper = QLineEdit(initial_upper_value)  # поле для верхней границы

                h_layout.addWidget(input_lower)  # добавляем поле для нижней границы в горизонтальный layout
                h_layout.addWidget(input_upper)  # добавляем поле для верхней границы в горизонтальный layout

                param_layout.addLayout(h_layout)  # добавляем горизонтальный layout в вертикальный layout

                layout.addLayout(param_layout)  # добавляем новый вертикальный layout в основной layout

                other_bounds_inputs[reaction][param] = (input_lower, input_upper)
            
            layout.addLayout(h_layout)
            group_box.setLayout(layout)
            main_layout.addWidget(group_box)
            main_layout.setStretchFactor(group_box, 1)            

        btn = QPushButton("Применить")
        btn.clicked.connect(dialog.accept)
        main_layout.addWidget(btn)

        dialog.setLayout(main_layout)

        if dialog.exec_():
            selected = {}
            bounds = {}
            other_bounds = {}
            for reaction in reactions:
                selected[reaction] = [peak_type for peak_type, checkbox in checkboxes[reaction].items() if checkbox.isChecked()]
                bounds[reaction] = {}                
                for peak_type, constraints in bounds_inputs[reaction].items():
                    bounds[reaction][peak_type] = {constraint: float(input_field.text()) for constraint, input_field in constraints.items()}
                
                other_bounds[reaction] = {}
                for param, (input_lower, input_upper) in other_bounds_inputs[reaction].items():
                    other_bounds[reaction][param] = (float(input_lower.text()), float(input_upper.text()))
                    
            selected_peak_types = [selected[reaction] for reaction in reactions]
            combinations = list(product(*selected_peak_types))
            
            logger.debug(f'selected combinations: {selected}')
            logger.debug(f'producted combinations: {combinations}')
            logger.debug(f'producted bounds: {bounds}')
            logger.debug(f'additional bounds: {other_bounds}')
            
            return selected, combinations, bounds, other_bounds
        else:
            return None, None, None, None

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
        dialog = self.create_dialog()
        reactions = self.data_handler.retrieve_table_data('gauss')['reaction']
        checkboxes, bounds_inputs, other_bounds_inputs = self.create_reaction_groups(dialog, reactions)
        
        if dialog.exec_():
            selected, combinations, bounds, other_bounds = self.extract_input_values(reactions, checkboxes, bounds_inputs, other_bounds_inputs)
            return selected, combinations, bounds, other_bounds
        else:
            return None, None, None, None
        
    def create_dialog(self):
        dialog = QDialog()
        dialog.setWindowTitle("Выбор типов пиков и ограничений")
        dialog.setLayout(QHBoxLayout())
        dialog.layout().setSpacing(0)
        return dialog
    
    def create_reaction_groups(self, dialog, reactions):
        checkboxes = {}
        bounds_inputs = {}
        other_bounds_inputs = {}
        
        for reaction in reactions:
            group_box, layout = self.create_group_box(reaction)
            checkboxes[reaction], bounds_inputs[reaction], other_bounds_inputs[reaction] = self.create_reaction_controls(layout, reaction)
            
            dialog.layout().addWidget(group_box)
            dialog.layout().setStretchFactor(group_box, 1)
        
        btn = QPushButton("Применить")
        btn.clicked.connect(dialog.accept)
        dialog.layout().addWidget(btn)
        
        return checkboxes, bounds_inputs, other_bounds_inputs
    
    def create_group_box(self, reaction):
        group_box = QGroupBox(reaction)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        group_box.setContentsMargins(10, 10, 10, 10)
        group_box.setLayout(layout)
        return group_box, layout

    def create_reaction_controls(self, layout, reaction):
        gauss_data = self.data_handler.retrieve_table_data('gauss')
        reaction_row = gauss_data[gauss_data['reaction'] == reaction]

        checkboxes = self.create_checkboxes(layout)
        bounds_inputs = self.create_bounds_inputs(layout, reaction_row)
        other_bounds_inputs = self.create_other_bounds_inputs(layout, reaction_row)
        
        return checkboxes, bounds_inputs, other_bounds_inputs

    def create_checkboxes(self, layout):
        checkboxes = {}
        for peak_type in ['gauss', 'fraser', 'ads']:
            checkbox = QCheckBox(peak_type)
            checkbox.setChecked(True)
            layout.addWidget(checkbox)
            checkboxes[peak_type] = checkbox
        return checkboxes

    def create_bounds_inputs(self, layout, reaction_row):
        constraint_to_column = {
            'a_bottom_constraint': 'coeff_a', 
            'a_top_constraint': 'coeff_a', 
            's1_bottom_constraint': 'coeff_s1', 
            's1_top_constraint': 'coeff_s1', 
            's2_bottom_constraint': 'coeff_s2', 
            's2_top_constraint': 'coeff_s2'
        }
        bounds_inputs = {}
        
        for peak_type in ['gauss', 'fraser', 'ads']:
            bounds_inputs[peak_type] = self.create_peak_type_bounds(peak_type, layout, reaction_row, constraint_to_column)
        return bounds_inputs

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
            
            for constraint in constraint_pair:
                coeff_column = constraint_to_column[constraint]
                initial_value = str(reaction_row[coeff_column].values[0]) if not reaction_row.empty else "0.0"
                input_field = QLineEdit(initial_value)
                h_layout.addWidget(input_field)
                bounds[constraint] = input_field
            layout.addLayout(h_layout)
        return bounds


    def create_other_bounds_inputs(self, layout, reaction_row):
        other_bounds_inputs = {}
        for param in ['height', 'center', 'width']:
            param_layout = QVBoxLayout()
            label = QLabel(f"{param}_bounds")
            param_layout.addWidget(label)
            
            h_layout = QHBoxLayout()
            initial_lower_value = str(np.round(reaction_row[param].values[0]*0.8, 3)) if not reaction_row.empty else "0.0"
            initial_upper_value = str(np.round(reaction_row[param].values[0]*1.2, 3)) if not reaction_row.empty else "0.0"
            
            input_lower = QLineEdit(initial_lower_value)
            input_upper = QLineEdit(initial_upper_value)
            
            h_layout.addWidget(input_lower)
            h_layout.addWidget(input_upper)
            
            param_layout.addLayout(h_layout)
            layout.addLayout(param_layout)
            other_bounds_inputs[param] = (input_lower, input_upper)
        return other_bounds_inputs

    def extract_input_values(self, reactions, checkboxes, bounds_inputs, other_bounds_inputs):
        selected = {}
        bounds = {}
        other_bounds = {}
        for reaction in reactions:
            selected[reaction] = [peak_type for peak_type, checkbox in checkboxes[reaction].items() if checkbox.isChecked()]
            bounds[reaction] = {peak_type: {constraint: float(input_field.text()) for constraint, input_field in constraints.items()} for peak_type, constraints in bounds_inputs[reaction].items()}
            other_bounds[reaction] = {param: (float(input_lower.text()), float(input_upper.text())) for param, (input_lower, input_upper) in other_bounds_inputs[reaction].items()}
            
        selected_peak_types = [selected[reaction] for reaction in reactions]
        combinations = list(product(*selected_peak_types))
        
        logger.debug(f'selected combinations: {selected}')
        logger.debug(f'producted combinations: {combinations}')
        logger.debug(f'producted bounds: {bounds}')
        logger.debug(f'additional bounds: {other_bounds}')
        
        return selected, combinations, bounds, other_bounds

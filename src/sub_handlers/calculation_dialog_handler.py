from PyQt5.QtWidgets import QDialog, QHBoxLayout, QGroupBox, QVBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton
import numpy as np
from src.logger_config import logger
from itertools import product


class UIDialogHandler():
    def __init__(self, data_handler):
        self.data_handler = data_handler

    def create_dialog(self):
        dialog = QDialog()
        dialog.setWindowTitle("Выбор типов пиков и ограничений")
        dialog.setLayout(QHBoxLayout())
        dialog.layout().setSpacing(0)
        return dialog
    
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
        
        calibration_btn = QPushButton("Калибровка")
        calibration_btn.clicked.connect(lambda: self.set_calibration(coeffs_bounds_inputs))
        dialog.layout().addWidget(calibration_btn)
        
        return checkboxes, coeffs_bounds_inputs, peaks_params_inputs    
    
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
        coeffs_bounds_inputs = self.create_coeffs_bounds_inputs(layout, reaction_row)
        peaks_params_inputs = self.create_peaks_params_inputs(layout, reaction_row)
        
        return checkboxes, coeffs_bounds_inputs, peaks_params_inputs

    def create_checkboxes(self, layout):
        checkboxes = {}
        for peak_type in ['gauss', 'fraser', 'ads']:
            checkbox = QCheckBox(peak_type)
            checkbox.setChecked(True)
            layout.addWidget(checkbox)
            checkboxes[peak_type] = checkbox
        return checkboxes

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

    def get_constraints(self, peak_type):
        if peak_type == 'fraser':
            return [('a_bottom_constraint', 'a_top_constraint')]
        elif peak_type == 'ads':
            return [('s1_bottom_constraint', 's1_top_constraint'), ('s2_bottom_constraint', 's2_top_constraint')]
        else:
            return []
        
    def get_initial_values(self, constraint, reaction_row, constraint_to_column, calibration=False):
        logger.debug(f"get_initial_values constraint: {constraint}, calibration: {calibration}")

        if calibration and reaction_row is not None and constraint_to_column is not None:
            base_value = float(reaction_row[constraint_to_column[constraint]].values[0]) if not reaction_row.empty else 0.0
            result = str(base_value * 0.8) if "bottom" in constraint else str(base_value * 1.2)
            logger.debug(f"Returning calibrated value: {result}")
            return result
        elif calibration:
            calibration_values = {
                'a_bottom_constraint': '-2',
                'a_top_constraint': '2',
                's1_bottom_constraint': '0.1',
                's2_bottom_constraint': '0.1',
                's1_top_constraint': '35',
                's2_top_constraint': '35'
            }
            result = calibration_values.get(constraint, "")
            logger.debug(f"get_initial_values calibration return value: {result}")
            return result
        else:
            base_value = float(reaction_row[constraint_to_column[constraint]].values[0]) if not reaction_row.empty else 0.0
            result = str(base_value * 0.8) if "bottom" in constraint else str(base_value * 1.2)
            logger.debug(f"get_initial_values base value: {result}")  # Добавлено для отладки
            return result
            
    def set_calibration(self, coeffs_bounds_inputs): 
        # Проходим по каждому типу пика (например, Reaction_1, Reaction_2, и т.д.)
        for peak_type, constraints in coeffs_bounds_inputs.items():
            logger.debug(f"Processing peak_type: {peak_type}")

            # Затем проходим по каждому типу ограничения (например, gauss, fraser, и т.д.)
            for constraint_type, input_fields in constraints.items():
                logger.debug(f"Processing constraint_type: {constraint_type}")

                # Если input_fields является словарем, проходим по его элементам
                if isinstance(input_fields, dict):
                    for constraint, input_field in input_fields.items():
                        # Проверяем, является ли input_field объектом QLineEdit
                        if isinstance(input_field, QLineEdit):
                            logger.debug(f"Setting value for input field {constraint} within bounds for constraint_type: {constraint_type}")
                            input_field.setText(self.get_initial_values(constraint, None, None, calibration=True))
    
    def create_peak_type_bounds(self, peak_type, layout, reaction_row, constraint_to_column):
        bounds = {}
        constraints = self.get_constraints(peak_type)
        for constraint_pair in constraints:
            h_layout = QHBoxLayout()
            label = QLabel(f"{constraint_pair[0].split('_')[0]}_coeff_bounds")
            layout.addWidget(label)
            
            for constraint in constraint_pair:
                initial_value = self.get_initial_values(constraint, reaction_row, constraint_to_column)
                input_field = QLineEdit(initial_value)
                h_layout.addWidget(input_field)
                bounds[constraint] = input_field
            
            layout.addLayout(h_layout)
        return bounds

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
    

class CalculationDialogHandler:
    def __init__(self, data_handler):
        self.data_handler = data_handler
        self.ui_handler = UIDialogHandler(self.data_handler)
    
    def fetch_peak_type_and_bounds(self):       
        dialog = self.ui_handler.create_dialog()
        reactions = self.data_handler.retrieve_table_data('gauss')['reaction']
        checkboxes, coeffs_bounds_inputs, peaks_params_inputs = self.ui_handler.create_reaction_groups(dialog, reactions)
        
        if dialog.exec_():
            selected, combinations, coeffs_bounds, peaks_params = self.extract_input_values(reactions, checkboxes, coeffs_bounds_inputs, peaks_params_inputs)
            return selected, combinations, coeffs_bounds, peaks_params
        else:
            return None, None, None, None
    
    def extract_input_values(self, reactions, checkboxes, coeffs_bounds_inputs, peaks_params_inputs):
        selected = {}
        coeffs_bounds = {}
        peaks_bounds = {}
        for reaction in reactions:            
            selected[reaction] = [peak_type for peak_type, checkbox in checkboxes[reaction].items() if checkbox.isChecked()]
            
            coeffs_bounds[reaction] = {
                peak_type: {constraint: float(input_field.text()) for constraint, input_field in constraints.items()
                            } for peak_type, constraints in coeffs_bounds_inputs[reaction].items()}
            
            peaks_bounds[reaction] = {
                param: (float(input_lower.text()), float(input_upper.text())) 
                for param, (input_lower, input_upper) in peaks_params_inputs[reaction].items()}
                
        selected_peak_types = [selected[reaction] for reaction in reactions]        
        combinations = list(product(*selected_peak_types))
        
        logger.debug(f'selected combinations: {selected}')
        logger.debug(f'producted combinations: {combinations}')
        logger.debug(f'producted bounds: {coeffs_bounds}')
        logger.debug(f'peaks params bounds: {peaks_bounds}')
        
        return selected, combinations, coeffs_bounds, peaks_bounds

    def extract_bounds_selected_combinations(self, selected_combinations, coeffs_bounds):
        
        result = []
        
        bounds_keys = {
            'fraser': [('a_bottom_constraint', 'a_top_constraint')],
            'ads': [('s1_bottom_constraint', 's1_top_constraint'),
                    ('s2_bottom_constraint', 's2_top_constraint')]
        }
        
        for reaction, functions in selected_combinations.items():            
            for func in functions:                
                if func in bounds_keys:                    
                    for bottom_key, top_key in bounds_keys[func]:                        
                        bounds = coeffs_bounds[reaction][func]                       
                        result.append((bounds[bottom_key], bounds[top_key]))
                        
        logger.debug(f'extracted_bounds: {result}')        
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

from PyQt5.QtWidgets import QApplication, QLineEdit, QInputDialog, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventHandler(QObject):
    update_console_signal = pyqtSignal(str)
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.viewer = main_app.viewer
        self.ui_initializer = main_app.ui_initializer
        self.table_manager = main_app.table_manager
        self.math_operations = main_app.math_operations 
   
    def add_diff_button_pushed(self):
        x_column_name = self.ui_initializer.combo_box_x.currentText()
        y_column_name = self.ui_initializer.combo_box_y.currentText()

        dy_dx = self.math_operations.compute_derivative(
            self.viewer.df[x_column_name],
            self.viewer.df[y_column_name])

        new_column_name = y_column_name + '_diff'
        self.viewer.df[new_column_name] = dy_dx

        self.table_manager.fill_table(self.viewer.file_name)

        self.table_manager.fill_combo_boxes(
            self.ui_initializer.combo_box_x,
            self.ui_initializer.combo_box_y) 

        self.ui_initializer.combo_box_y.setCurrentText(new_column_name)

    def get_init_params(self):
        logger.debug("Начало метода get_init_params.")        
        init_params = []
        for index, row in self.table_manager.data['gauss'].iterrows():
            logger.debug(f"Обработка строки {index}: height={row['height']}, center={row['center']}, width={row['width']}")
            init_params.extend([row['height'], row['center'], row['width']])
        logger.debug(f"Длина начальных параметров: {len(init_params)}")
        logger.debug(f"Конец метода get_init_params. Полученные параметры: {str(init_params)}.")
        return init_params

    def update_gaussian_data(self, best_params, best_combination, coeff_1):
        logger.debug("Начало метода update_gaussian_data.")
        gaussian_data = self.table_manager.data['gauss'].copy()

        for i, peak_type in enumerate(best_combination):
            height = best_params[3 * i]
            center = best_params[3 * i + 1]
            width = best_params[3 * i + 2]
            coeff_ = coeff_1[i]

            gaussian_data.at[i, 'height'] = height
            gaussian_data.at[i, 'center'] = center
            gaussian_data.at[i, 'width'] = width
            gaussian_data.at[i, 'type'] = peak_type
            gaussian_data.at[i, 'coeff_1'] = coeff_

        return gaussian_data
    
    def add_reaction_cummulative_func(self, best_params, best_combination, x_values, y_column, cummulative_func):
        logger.debug("Начало метода add_reaction_cummulative_func.")
        for i, peak_type in enumerate(best_combination):
            height = best_params[3 * i]
            center = best_params[3 * i + 1]
            width = best_params[3 * i + 2]  
            
            new_column_name = y_column + '_reaction_' + str(i)
            if peak_type == 'gauss':
                peak_func = self.math_operations.gaussian(x_values, height, center, width)
            else:
                peak_func = self.math_operations.fraser_suzuki(
                    x_values, height, center, width, 
                    float(self.table_manager.data['options']['coeff_1'].values))
                
            self.viewer.df[new_column_name] = peak_func
            cummulative_func += peak_func

        new_column_name = y_column + '_cummulative'
        self.viewer.df[new_column_name] = cummulative_func
        logger.debug("Конец метода add_reaction_cummulative_func.")

    def compute_peaks_button_pushed(self, coeff_1: list[float]):
        coefficients_str = ', '.join(map(str, coeff_1))
        self.main_app.ui_initializer.console_widget.append(f'Получены коэффициенты: {coefficients_str}')
        QApplication.processEvents()


        logger.info(f'Получены коэффициенты: {str(coeff_1)}')
        x_column_name = self.ui_initializer.combo_box_x.currentText() 
        y_column_name = self.ui_initializer.combo_box_y.currentText() 
        init_params = self.get_init_params()
        x_values = self.table_manager.get_column_data(x_column_name)
        y_values = self.table_manager.get_column_data(y_column_name)

        maxfev = int(self.table_manager.data['options']['maxfev'].values)        
        num_peaks = len(init_params) // 3
        best_params, best_combination, best_rmse = self.math_operations.compute_best_peaks(
        x_values, y_values, num_peaks, init_params, maxfev, coeff_1)
        
        cummulative_func = np.zeros(len(x_values))
        self.main_app.ui_initializer.console_widget.append(f'Лучшее значение RMSE: {best_rmse}')
               
        best_gaussian_data = self.update_gaussian_data(best_params, best_combination, coeff_1)
        self.table_manager.update_table_data('gauss', best_gaussian_data)
        
        self.add_reaction_cummulative_func(
            best_params, best_combination, x_values, y_column_name, cummulative_func)
        
        self.table_manager.data['options']['rmse'] = best_rmse                              
        
        self.rebuild_gaussians()
        
        self.table_manager.fill_table('gauss')
        return best_rmse
        
    def connect_signals(self):  
        self.table_manager.tables['gauss'].clicked.connect(self.handle_table_clicked)
        self.table_manager.tables['options'].clicked.connect(self.handle_table_clicked)
        if self.viewer.file_name:
            self.table_manager.tables[self.viewer.file_name].clicked.connect(self.handle_table_clicked)

    def handle_table_clicked(self, q_model_index):
        table = self.table_manager.tables[self.table_manager.current_table_name]
        model = table.model()

        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            self.table_manager.delete_row(q_model_index.row())
            self.rebuild_gaussians()
        elif QApplication.keyboardModifiers() == Qt.AltModifier:
            self.table_manager.delete_column(q_model_index.column())
        else:
            # Получаем текущее значение из модели
            current_value = model.data(q_model_index, Qt.DisplayRole)

            # Здесь можно выполнить необходимые действия для изменения значения, например, показать диалоговое окно для ввода нового значения.
            new_value, ok = QInputDialog.getText(None, "Изменить значение", "Введите новое значение:", QLineEdit.Normal, current_value)
            if ok and new_value != current_value:
                # Устанавливаем новое значение в модели
                model.set_data(q_model_index, new_value, Qt.EditRole)
        
    def on_release(self, event):
        """Обработка отпускания кнопки мыши."""
        release_x = event.xdata
        width = 2 * abs(release_x - self.press_x)
        x_column_data = self.table_manager.get_column_data(self.ui_initializer.combo_box_x.currentText())
        x = np.linspace(min(x_column_data), max(x_column_data), 1000)
        y = self.math_operations.gaussian(x, self.press_y, self.press_x, width)

        ax = self.ui_initializer.figure1.get_axes()[0]
        ax.plot(x, y, 'r-')
        self.ui_initializer.canvas1.draw()

        self.table_manager.add_gaussian_to_table(self.press_y, self.press_x, width)
        
    def on_press(self, event):
        """Обработка нажатия кнопки мыши на оси."""
        self.press_x = event.xdata
        self.press_y = event.ydata

    def connect_canvas_events(self):
        self.table_manager.fill_table('gauss')       
        
        self.press_cid = self.ui_initializer.canvas1.mpl_connect('button_press_event', self.on_press)
        self.release_cid = self.ui_initializer.canvas1.mpl_connect('button_release_event', self.on_release)

    def disconnect_canvas_events(self):        
        self.table_manager.fill_table(self.viewer.file_name)        
        
        self.ui_initializer.canvas1.mpl_disconnect(self.press_cid)
        self.ui_initializer.canvas1.mpl_disconnect(self.release_cid)
        
        self.rebuild_gaussians()

    def rebuild_gaussians(self):
        """Перестроение всех гауссиан по данным в таблице."""
        self.plot_graph()  
        ax = self.ui_initializer.figure1.get_axes()[0]
        cumfunc = np.zeros(1000)
        for _, row in self.table_manager.data['gauss'].iterrows(): 
            x_column_data = self.table_manager.get_column_data(self.ui_initializer.combo_box_x.currentText()) 
            x = np.linspace(min(x_column_data), max(x_column_data), 1000)
            if row['type'] == 'gauss':
                y = self.math_operations.gaussian(x, row['height'], row['center'], row['width'])
            else:
                y = self.math_operations.fraser_suzuki(
                    x, float(row['height']), float(row['center']), float(row['width']), float(row['coeff_1']))
                _coef = str(row['coeff_1'])
                logger.info(f'В rebuild_gaussians коэффициент = {_coef}')
            ax.plot(x, y,)
            cumfunc += y
        ax.plot(x, cumfunc,)
        self.ui_initializer.canvas1.draw()
        
    def plot_graph(self):
        """Построение графика."""
        x_column = self.ui_initializer.combo_box_x.currentText() 
        y_column = self.ui_initializer.combo_box_y.currentText() 

        if not x_column or not y_column:  
            return

        self.ui_initializer.figure1.clear() 

        ax = self.ui_initializer.figure1.add_subplot(111) 
        ax.plot(self.viewer.df[x_column], self.viewer.df[y_column], 'b-')

        self.ui_initializer.canvas1.draw()
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import numpy as np

class EventHandler:
    def __init__(self, main_app):
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

        self.table_manager.fill_main_table()

        self.table_manager.fill_combo_boxes(
            self.ui_initializer.combo_box_x,
            self.ui_initializer.combo_box_y) 

        self.ui_initializer.combo_box_y.setCurrentText(new_column_name)

    def get_init_params(self):
        init_params = []
        for _, row in self.table_manager.gaussian_data.iterrows():
            init_params.extend([row['Height'], row['Center'], row['Width']])
        return init_params

    def update_gaussian_data(self, best_params, best_combination):
        for i, peak_type in enumerate(best_combination):
            a0 = best_params[3*i]
            a1 = best_params[3*i+1]
            a2 = best_params[3*i+2]
            self.table_manager.gaussian_data.at[i, 'Height'] = a0
            self.table_manager.gaussian_data.at[i, 'Center'] = a1
            self.table_manager.gaussian_data.at[i, 'Width'] = a2
            self.table_manager.gaussian_data.at[i, 'Type'] = peak_type
    
    def add_reaction_cummulative_func(self, best_params, best_combination, x_values, y_column, cummulative_func):
        for i, peak_type in enumerate(best_combination):
            a0 = best_params[3 * i]
            a1 = best_params[3 * i + 1]
            a2 = best_params[3 * i + 2]

            new_column_name = y_column + '_reaction_' + str(i)
            if peak_type == 'gauss':
                peak_func = self.math_operations.gaussian(x_values, a0, a1, a2)
            else:
                peak_func = self.math_operations.fraser_suzuki(x_values, a0, a1, a2, -1)
            self.viewer.df[new_column_name] = peak_func
            cummulative_func += peak_func

        new_column_name = y_column + '_cummulative'
        self.viewer.df[new_column_name] = cummulative_func

    def compute_peaks_button_pushed(self):
        x_column_name = self.ui_initializer.combo_box_x.currentText() 
        y_column_name = self.ui_initializer.combo_box_y.currentText() 
        init_params = self.get_init_params()
        x_values = self.table_manager.get_column_data(x_column_name)
        y_values = self.table_manager.get_column_data(y_column_name)

        best_params, best_combination, best_rmse = self.math_operations.compute_best_peaks(
            x_values, y_values, init_params)
        
        cummulative_func = np.zeros(len(x_values))

        self.update_gaussian_data(best_params, best_combination)
        
        self.add_reaction_cummulative_func(
            best_params, best_combination, x_values, y_column_name, cummulative_func)
                
        self.table_manager.fill_gauss_table()
        self.table_manager.fill_main_table()
        self.rebuild_gaussians()
        
    def connect_signals(self):  
        self.table_manager.gaussian_table.clicked.connect(self.handle_table_clicked)
        self.table_manager.csv_table.clicked.connect(self.handle_table_clicked)

    def handle_table_clicked(self, q_model_index):
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            self.table_manager.delete_row(q_model_index.row())
        elif QApplication.keyboardModifiers() == Qt.AltModifier:
            self.table_manager.delete_column(q_model_index.column())
        
    def on_release(self, event):
        """Обработка отпускания кнопки мыши."""
        release_x = event.xdata
        width = 2 * abs(release_x - self.press_x)
        x_column_data = self.table_manager.get_column_data(self.ui_initializer.combo_box_x.currentText())
        x = np.linspace(min(x_column_data), max(x_column_data), 1000)
        y = self.math_operations.gaussian(x, self.press_y, self.press_x, width)

        ax = self.ui_initializer.figure.get_axes()[0]
        ax.plot(x, y, 'r-')
        self.ui_initializer.canvas.draw()

        self.table_manager.add_gaussian_to_table(self.press_y, self.press_x, width)
        
    def on_press(self, event):
        """Обработка нажатия кнопки мыши на оси."""
        self.press_x = event.xdata
        self.press_y = event.ydata

    def connect_canvas_events(self):
        self.table_manager.stacked_widget.setCurrentIndex(1)
        self.press_cid = self.ui_initializer.canvas.mpl_connect('button_press_event', self.on_press)
        self.release_cid = self.ui_initializer.canvas.mpl_connect('button_release_event', self.on_release)

    def disconnect_canvas_events(self):
        self.table_manager.stacked_widget.setCurrentIndex(0)
        self.ui_initializer.canvas.mpl_disconnect(self.press_cid)
        self.ui_initializer.canvas.mpl_disconnect(self.release_cid)
        self.rebuild_gaussians()

    def rebuild_gaussians(self):
        """Перестроение всех гауссиан по данным в таблице."""
        self.plot_graph()  
        ax = self.ui_initializer.figure.get_axes()[0] 
        for _, row in self.table_manager.gaussian_data.iterrows(): 
            x_column_data = self.table_manager.get_column_data(self.ui_initializer.combo_box_x.currentText()) 
            x = np.linspace(min(x_column_data), max(x_column_data), 1000)
            if row['Type'] == 'gauss':
                y = self.math_operations.gaussian(x, row['Height'], row['Center'], row['Width'])
            else:
                y = self.math_operations.fraser_suzuki(x, row['Height'], row['Center'], row['Width'], -1)
            ax.plot(x, y, 'r-')

        self.ui_initializer.canvas.draw()
        
    def plot_graph(self):
        """Построение графика."""
        x_column = self.ui_initializer.combo_box_x.currentText() 
        y_column = self.ui_initializer.combo_box_y.currentText() 

        if not x_column or not y_column:  
            return

        self.ui_initializer.figure.clear() 

        ax = self.ui_initializer.figure.add_subplot(111) 
        ax.plot(self.viewer.df[x_column], self.viewer.df[y_column], 'b-')

        self.ui_initializer.canvas.draw()
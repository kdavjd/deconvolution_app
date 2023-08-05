from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import numpy as np

class EventHandler:
    def __init__(self, main_app):  # Было: mainApp
        self.main_app = main_app  # Было: mainApp

    def add_diff_button_pushed(self):
        x_column_name = self.main_app.ui_initializer.combo_box_x.currentText()
        y_column_name = self.main_app.ui_initializer.combo_box_y.currentText()
        
        dy_dx = self.main_app.math_operations.compute_derivative(
            self.main_app.viewer.df[x_column_name],
            self.main_app.viewer.df[y_column_name])
        
        new_column_name = y_column_name + '_diff'
        self.main_app.viewer.df[new_column_name] = dy_dx
        
        self.main_app.table_manager.fill_main_table()
        
        self.main_app.table_manager.fill_combo_boxes(
            self.main_app.ui_initializer.combo_box_x,
            self.main_app.ui_initializer.combo_box_y) 
        
        self.main_app.ui_initializer.combo_box_y.setCurrentText(new_column_name)
    
    def get_init_params(self):
        init_params = []
        for _, row in self.main_app.table_manager.gaussian_data.iterrows():
            init_params.extend([row['Height'], row['Center'], row['Width']])
        return init_params

    def update_gaussian_data(self, best_params, best_combination):
        for i, peak_type in enumerate(best_combination):
            a0 = best_params[3*i]
            a1 = best_params[3*i+1]
            a2 = best_params[3*i+2]
            self.main_app.table_manager.gaussian_data.at[i, 'Height'] = a0
            self.main_app.table_manager.gaussian_data.at[i, 'Center'] = a1
            self.main_app.table_manager.gaussian_data.at[i, 'Width'] = a2
            self.main_app.table_manager.gaussian_data.at[i, 'Type'] = peak_type
    
    def add_reaction_cummulative_func(self, best_params, best_combination, x_values, y_column, cummulative_func):
        for i, peak_type in enumerate(best_combination):
            a0 = best_params[3 * i]
            a1 = best_params[3 * i + 1]
            a2 = best_params[3 * i + 2]

            new_column_name = y_column + '_reaction_' + str(i)
            if peak_type == 'gauss':
                peak_func = self.main_app.math_operations.gaussian(x_values, a0, a1, a2)
            else:
                peak_func = self.main_app.math_operations.fraser_suzuki(x_values, a0, a1, a2, -1)
            self.main_app.viewer.df[new_column_name] = peak_func
            cummulative_func += peak_func

        new_column_name = y_column + '_cummulative'
        self.main_app.viewer.df[new_column_name] = cummulative_func
    
    def compute_peaks_button_pushed(self):
        x_column_name = self.main_app.ui_initializer.combo_box_x.currentText() 
        y_column_name = self.main_app.ui_initializer.combo_box_y.currentText() 
        init_params = self.get_init_params()
        x_values = self.main_app.table_manager.get_column_data(x_column_name)
        y_values = self.main_app.table_manager.get_column_data(y_column_name)

        best_params, best_combination, best_rmse = self.main_app.math_operations.compute_best_peaks(
            x_values, y_values, init_params)
        
        cummulative_func = np.zeros(len(x_values))

        self.update_gaussian_data(best_params, best_combination)
        
        self.add_reaction_cummulative_func(
            best_params, best_combination, x_values, y_column_name, cummulative_func)
                
        self.main_app.table_manager.fill_gauss_table()
        self.main_app.table_manager.fill_main_table()
        self.rebuild_gaussians()
        
    def connect_signals(self):  # Было: connectSignals
        self.main_app.table_manager.gaussian_table.clicked.connect(self.handle_table_clicked)  # Было: handleTableClicked
        self.main_app.table_manager.csv_table.clicked.connect(self.handle_table_clicked)  # Было: handleTableClicked

    def handle_table_clicked(self, q_model_index):  # Было: handleTableClicked
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            self.main_app.table_manager.delete_row(q_model_index.row())  # Было: deleteRow
        elif QApplication.keyboardModifiers() == Qt.AltModifier:
            self.main_app.table_manager.delete_column(q_model_index.column())  # Было: deleteColumn
    
    def on_release(self, event):  # Было: onRelease
        """Обработка отпускания кнопки мыши."""
        release_x = event.xdata
        width = 2 * abs(release_x - self.press_x)
        x_column_data = self.main_app.table_manager.get_column_data(self.main_app.ui_initializer.combo_box_x.currentText())  # Было: uiInitializer
        x = np.linspace(min(x_column_data), max(x_column_data), 1000)
        y = self.main_app.math_operations.gaussian(x, self.press_y, self.press_x, width)

        ax = self.main_app.ui_initializer.figure.get_axes()[0]  # Было: uiInitializer
        ax.plot(x, y, 'r-')
        self.main_app.ui_initializer.canvas.draw()  # Было: uiInitializer

        self.main_app.table_manager.add_gaussian_to_table(self.press_y, self.press_x, width)  # Было: add_gaussian_to_table
    
    def on_press(self, event):  # Было: onPress
        """Обработка нажатия кнопки мыши на оси."""
        self.press_x = event.xdata
        self.press_y = event.ydata

    def connect_canvas_events(self):  # Было: connectCanvasEvents
        self.main_app.table_manager.stacked_widget.setCurrentIndex(1)
        self.press_cid = self.main_app.ui_initializer.canvas.mpl_connect('button_press_event', self.on_press)  # Было: onPress, uiInitializer
        self.release_cid = self.main_app.ui_initializer.canvas.mpl_connect('button_release_event', self.on_release)  # Было: onRelease, uiInitializer

    def disconnect_canvas_events(self):  # Было: disconnectCanvasEvents
        self.main_app.table_manager.stacked_widget.setCurrentIndex(0)
        self.main_app.ui_initializer.canvas.mpl_disconnect(self.press_cid)  # Было: uiInitializer
        self.main_app.ui_initializer.canvas.mpl_disconnect(self.release_cid)  # Было: uiInitializer
        self.main_app.rebuild_gaussians()  # Было: rebuildGaussians

    def rebuild_gaussians(self):
        """Перестроение всех гауссиан по данным в таблице."""
        self.plot_graph()  # очистим график # Было: plotGraph
        ax = self.main_app.ui_initializer.figure.get_axes()[0] # Было: uiInitializer
        for _, row in self.main_app.table_manager.gaussian_data.iterrows(): # Было: tableManager
            x_column_data = self.main_app.table_manager.get_column_data(self.main_app.ui_initializer.combo_box_x.currentText()) # Было: tableManager, uiInitializer, comboBoxX
            x = np.linspace(min(x_column_data), max(x_column_data), 1000)
            if row['Type'] == 'gauss':
                y = self.main_app.math_operations.gaussian(x, row['Height'], row['Center'], row['Width'])
            else:
                y = self.main_app.math_operations.fraser_suzuki(x, row['Height'], row['Center'], row['Width'], -1)
            ax.plot(x, y, 'r-')

        self.main_app.ui_initializer.canvas.draw()
        
        
    def plot_graph(self): # Было: plotGraph
        """Построение графика."""
        x_column = self.main_app.ui_initializer.combo_box_x.currentText() # Было: uiInitializer, comboBoxX
        y_column = self.main_app.ui_initializer.combo_box_y.currentText() # Было: uiInitializer, comboBoxY

        if not x_column or not y_column:  # Если одно из значений пустое, прекратить функцию
            return

        self.main_app.ui_initializer.figure.clear() # Было: uiInitializer

        ax = self.main_app.ui_initializer.figure.add_subplot(111) # Было: uiInitializer
        ax.plot(self.main_app.viewer.df[x_column], self.main_app.viewer.df[y_column], 'b-')

        self.main_app.ui_initializer.canvas.draw()
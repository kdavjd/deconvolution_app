from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import numpy as np

class EventHandler:
    def __init__(self, main_app):  # Было: mainApp
        self.main_app = main_app  # Было: mainApp

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

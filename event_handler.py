from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import numpy as np

class EventHandler:
    def __init__(self, mainApp):
        self.mainApp = mainApp

    def connectSignals(self):
        self.mainApp.tableManager.gaussian_table.clicked.connect(self.handleTableClicked)
        self.mainApp.tableManager.csv_table.clicked.connect(self.handleTableClicked)

    def handleTableClicked(self, qModelIndex):
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            self.mainApp.tableManager.deleteRow(qModelIndex.row())
        elif QApplication.keyboardModifiers() == Qt.AltModifier:
            self.mainApp.tableManager.deleteColumn(qModelIndex.column())
    
    def onRelease(self, event):
        """Обработка отпускания кнопки мыши."""
        release_x = event.xdata
        width = 2 * abs(release_x - self.press_x)
        x_column_data = self.mainApp.get_column_data(self.mainApp.uiInitializer.comboBoxX.currentText())
        x = np.linspace(min(x_column_data), max(x_column_data), 1000)
        y = self.mainApp.math_operations.gaussian(x, self.press_y, self.press_x, width)

        ax = self.mainApp.uiInitializer.figure.get_axes()[0]
        ax.plot(x, y, 'r-')
        self.mainApp.uiInitializer.canvas.draw()
        
        self.mainApp.tableManager.add_gaussian_to_table(self.press_y, self.press_x, width)
    
    def onPress(self, event):
        """Обработка нажатия кнопки мыши на оси."""
        self.press_x = event.xdata
        self.press_y = event.ydata
    
    def connectCanvasEvents(self):
        self.mainApp.tableManager.stacked_widget.setCurrentIndex(1)
        self.press_cid = self.mainApp.uiInitializer.canvas.mpl_connect('button_press_event', self.onPress)
        self.release_cid = self.mainApp.uiInitializer.canvas.mpl_connect('button_release_event', self.onRelease)

    def disconnectCanvasEvents(self):
        self.mainApp.tableManager.stacked_widget.setCurrentIndex(0)
        self.mainApp.uiInitializer.canvas.mpl_disconnect(self.press_cid)
        self.mainApp.uiInitializer.canvas.mpl_disconnect(self.release_cid)
        self.mainApp.rebuildGaussians()

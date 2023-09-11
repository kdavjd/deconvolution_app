from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout, QLabel, QLineEdit, QGroupBox
from PyQt5.QtCore import QObject, pyqtSignal
from src.sub_handlers.graph_handler import GraphHandler
from src.sub_handlers.data_handler import DataHandler
from src.sub_handlers.ui_handler import UIHandler
from src.sub_handlers.calculation_dialog_handler import CalculationDialogHandler

from src.logger_config import logger


class EventHandler(QObject):
    update_console_signal = pyqtSignal(str)
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.graph_handler = GraphHandler(main_app)
        self.data_handler = DataHandler(main_app)
        self.ui_handler = UIHandler(main_app)
        self.calculation_dialog_handler = CalculationDialogHandler(self.data_handler)
    
    
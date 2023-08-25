from PyQt5.QtWidgets import QApplication, QLineEdit, QInputDialog, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject, pyqtSignal
from src.sub_handlers.graph_handler import GraphHandler
from src.sub_handlers.data_handler import DataHandler
from src.sub_handlers.ui_handler import UIHandler

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventHandler(QObject):
    update_console_signal = pyqtSignal(str)
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.graph_handler = GraphHandler(main_app)
        self.data_handler = DataHandler(main_app)
        self.ui_handler = UIHandler(main_app) 
 

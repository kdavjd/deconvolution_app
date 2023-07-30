from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QComboBox, QLabel
from PyQt5.QtCore import QSize
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class UIInitializer(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.setMinimumSize(QSize(1080, 920))  

        self.buttonLoadCSV = QPushButton('Load CSV', self)
        self.buttonLoadCSV.clicked.connect(parent.getCSV)

        self.labelX = QLabel('Select X:', self)
        self.comboBoxX = QComboBox()

        self.labelY = QLabel('Select Y:', self)
        self.comboBoxY = QComboBox()
        
        self.comboBoxX.currentIndexChanged.connect(parent.plotGraph)
        self.comboBoxY.currentIndexChanged.connect(parent.plotGraph)

        self.buttonInteractive = QPushButton('Interactive Mode', self)
        self.buttonInteractive.setCheckable(True)
        self.buttonInteractive.clicked.connect(parent.interactiveMode)

        self.buttonAddDiff = QPushButton('Add Diff', self)
        self.buttonAddDiff.clicked.connect(parent.addDiff)

        self.figure = Figure()
        self.figure.set_size_inches(10, 5, forward=True)
        self.canvas = FigureCanvas(self.figure)

        self.buttonDeleteColumn = QPushButton('Delete X column', self)
        self.buttonDeleteColumn.clicked.connect(parent.deleteColumn)

        main_layout = QVBoxLayout()

        top_layout = QHBoxLayout()

        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.buttonLoadCSV)
        buttons_layout.addWidget(self.buttonInteractive)
        buttons_layout.addWidget(self.buttonAddDiff)
        buttons_layout.addWidget(self.buttonDeleteColumn)
        buttons_layout.addWidget(self.labelX)
        buttons_layout.addWidget(self.comboBoxX)        
        buttons_layout.addWidget(self.labelY)
        buttons_layout.addWidget(self.comboBoxY)        

        top_layout.addLayout(buttons_layout)

        top_layout.addWidget(parent.tableManager.stacked_widget)

        main_layout.addLayout(top_layout)

        main_layout.addWidget(self.canvas)

        self.setLayout(main_layout)

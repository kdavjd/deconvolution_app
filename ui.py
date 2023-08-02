from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QComboBox, QLabel, QSplitter
from PyQt5.QtCore import QSize, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class UIInitializer(QWidget):
    def __init__(self, parent, viewer): 
        super().__init__(parent)

        # Установка минимального размера окна
        self.setMinimumSize(QSize(1080, 920))  

        # Создание кнопок и выпадающих списков
        self.buttonLoadCSV = QPushButton('Load CSV', self)
        self.buttonLoadCSV.clicked.connect(viewer.getCSV) 

        self.buttonExportCSV = QPushButton('Export CSV', self)
        self.buttonExportCSV.clicked.connect(viewer.exportCSV)     
        
        self.buttonDeleteColumn = QPushButton('Delete X column', self)
        self.buttonDeleteColumn.clicked.connect(parent.deleteColumn)

        self.buttonComputePeaks = QPushButton('Compute peaks', self)
        self.buttonComputePeaks.clicked.connect(parent.computePeaks)  

        self.comboBoxX = QComboBox()
        self.comboBoxX.addItem("Select X") # Placeholder for X selection        

        self.comboBoxY = QComboBox()
        self.comboBoxY.addItem("Select Y") # Placeholder for Y selection
        
        # Связывание изменений в выпадающих списках с функцией plotGraph
        self.comboBoxX.currentIndexChanged.connect(parent.plotGraph)
        self.comboBoxY.currentIndexChanged.connect(parent.plotGraph)

        self.buttonInteractive = QPushButton('Interactive Mode', self)
        self.buttonInteractive.setCheckable(True)
        self.buttonInteractive.clicked.connect(parent.switchToInteractiveMode)

        self.buttonAddDiff = QPushButton('Add Diff', self)
        self.buttonAddDiff.clicked.connect(parent.addDiff)

        # Создание блока с кнопками и выпадающими списками
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.buttonLoadCSV)
        buttons_layout.addWidget(self.buttonExportCSV)
        buttons_layout.addWidget(self.buttonDeleteColumn)
        buttons_layout.addWidget(self.buttonComputePeaks)
        buttons_layout.addWidget(self.buttonInteractive)
        buttons_layout.addWidget(self.buttonAddDiff)
        buttons_layout.addWidget(self.comboBoxX)
        buttons_layout.addWidget(self.comboBoxY)

        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)

        # Создание блока с таблицей
        table_layout = QVBoxLayout()
        table_layout.addWidget(parent.tableManager.stacked_widget)
        table_widget = QWidget()
        table_widget.setLayout(table_layout)

        # Создание блока с графиком
        self.figure = Figure()
        self.figure.set_size_inches(10, 5, forward=True)
        self.canvas = FigureCanvas(self.figure)
        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.canvas)
        graph_widget = QWidget()
        graph_widget.setLayout(graph_layout)

        # Создание вертикального разделителя с блоками
        splitterVertical = QSplitter(Qt.Vertical)
        splitterVertical.addWidget(table_widget)
        splitterVertical.addWidget(graph_widget)

        # Создание горизонтального разделителя с блоками
        splitterHorizontal = QSplitter(Qt.Horizontal)
        splitterHorizontal.addWidget(buttons_widget)
        splitterHorizontal.addWidget(splitterVertical)

        # Добавление разделителей на главный layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitterHorizontal)

        # Установка главного layout
        self.setLayout(main_layout)

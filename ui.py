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
        self.button_load_csv = QPushButton('Load CSV', self)  # Было: buttonLoadCSV
        self.button_load_csv.clicked.connect(viewer.get_csv)  # Было: getCSV

        self.button_export_csv = QPushButton('Export CSV', self)  # Было: buttonExportCSV
        self.button_export_csv.clicked.connect(viewer.export_csv)  # Было: exportCSV      

        self.button_compute_peaks = QPushButton('Compute peaks', self)  # Было: buttonComputePeaks
        self.button_compute_peaks.clicked.connect(parent.compute_peaks)  # Было: computePeaks

        self.combo_box_x = QComboBox()  # Было: comboBoxX
        self.combo_box_x.addItem("Select X") # Placeholder for X selection        

        self.combo_box_y = QComboBox()  # Было: comboBoxY
        self.combo_box_y.addItem("Select Y") # Placeholder for Y selection
        
        # Связывание изменений в выпадающих списках с функцией plot_graph
        self.combo_box_x.currentIndexChanged.connect(parent.plot_graph)  # Было: plotGraph
        self.combo_box_y.currentIndexChanged.connect(parent.plot_graph)  # Было: plotGraph

        self.button_interactive = QPushButton('Interactive Mode', self)  # Было: buttonInteractive
        self.button_interactive.setCheckable(True)
        self.button_interactive.clicked.connect(parent.switch_to_interactive_mode)  # Было: switchToInteractiveMode

        self.button_add_diff = QPushButton('Add Diff', self)  # Было: buttonAddDiff
        self.button_add_diff.clicked.connect(parent.add_diff)  # Было: addDiff

        # Создание блока с кнопками и выпадающими списками
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.button_load_csv)
        buttons_layout.addWidget(self.button_export_csv)        
        buttons_layout.addWidget(self.button_compute_peaks)
        buttons_layout.addWidget(self.button_interactive)
        buttons_layout.addWidget(self.button_add_diff)
        buttons_layout.addWidget(self.combo_box_x)
        buttons_layout.addWidget(self.combo_box_y)

        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)

        # Создание блока с таблицей
        table_layout = QVBoxLayout()
        table_layout.addWidget(parent.table_manager.stacked_widget)  # Было: tableManager
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
        splitter_vertical = QSplitter(Qt.Vertical)  # Было: splitterVertical
        splitter_vertical.addWidget(table_widget)
        splitter_vertical.addWidget(graph_widget)

        # Создание горизонтального разделителя с блоками
        splitter_horizontal = QSplitter(Qt.Horizontal)  # Было: splitterHorizontal
        splitter_horizontal.addWidget(buttons_widget)
        splitter_horizontal.addWidget(splitter_vertical)

        # Добавление разделителей на главный layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter_horizontal)

        # Установка главного layout
        self.setLayout(main_layout)

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QComboBox, QLabel, QSplitter, QTabWidget
from PyQt5.QtCore import QSize, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class UIInitializer(QWidget):
    def __init__(self, parent, viewer): 
        super().__init__(parent)

        # Установка минимального размера окна
        self.setMinimumSize(QSize(1220, 920))  

        # Создание кнопок и выпадающих списков
        self.button_load_csv = QPushButton('Load CSV', self)  # Было: buttonLoadCSV
        self.button_load_csv.clicked.connect(parent.load_csv_table)  # Было: getCSV

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

        self.button_options_mode = QPushButton('Options Mode', self)  # Новая кнопка
        self.button_options_mode.clicked.connect(parent.options_mode)
        
        # Создание блока с кнопками и выпадающими списками
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.button_load_csv)
        buttons_layout.addWidget(self.button_export_csv)
        buttons_layout.addWidget(self.button_options_mode)     
        buttons_layout.addWidget(self.button_compute_peaks)
        buttons_layout.addWidget(self.button_interactive)
        buttons_layout.addWidget(self.button_add_diff)
        buttons_layout.addWidget(self.combo_box_x)
        buttons_layout.addWidget(self.combo_box_y)

        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)

        # Создание вкладок
        tab_widget = QTabWidget()
        
        # Создание блока с таблицей
        table_layout = QVBoxLayout()
        table_layout.addWidget(parent.table_manager.stacked_widget)  # Было: tableManager
        table_widget = QWidget()
        table_widget.setLayout(table_layout)

        # Создание блока с графиком для вкладки 1,2
        graph_widget1, self.canvas1, self.figure1 = self.create_graph_widget()
        graph_widget2, self.canvas2, self.figure2 = self.create_graph_widget()


        # Создание вертикального разделителя с блоками
        splitter_vertical = QSplitter(Qt.Vertical)  # Было: splitterVertical
        splitter_vertical.addWidget(table_widget)
        splitter_vertical.addWidget(tab_widget)

        # Создание горизонтального разделителя с блоками
        splitter_horizontal = QSplitter(Qt.Horizontal)  # Было: splitterHorizontal
        splitter_horizontal.addWidget(buttons_widget)
        splitter_horizontal.addWidget(splitter_vertical)

        # Добавление разделителей на главный layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter_horizontal)

        # Создание блока с таблицей
        table_widget1 = self.create_table_widget1(parent)

        # Вкладка 1: оси и таблица в столбец
        splitter_vertical1 = QSplitter(Qt.Vertical)
        splitter_vertical1.addWidget(table_widget1)
        splitter_vertical1.addWidget(graph_widget1)

        logger.debug("Table widget 1: %s", table_widget1)  # Лог для отладки
        logger.debug("Graph widget 1: %s", graph_widget1)  # Лог для отладки

        # Вкладка 2: только оси        
        logger.debug("Graph widget 2: %s", graph_widget2)  # Лог для отладки

        # Вкладка 3: только таблица
        table_widget3 = None
        logger.debug("Table widget 3: %s", table_widget3)  # Лог для отладки

        # Добавление вкладок в widget вкладок
        tab_widget.addTab(splitter_vertical1, "Axes & Table")
        tab_widget.addTab(graph_widget2, "Axes Only")
        tab_widget.addTab(table_widget3, "Table Only")

        # Создание главного разделителя
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(buttons_widget)
        main_splitter.addWidget(tab_widget)

        # Установка размеров областей
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 4)

        # Добавление разделителей на главный layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(main_splitter)

        # Установка главного layout
        self.setLayout(main_layout)

    def create_table_widget1(self, parent):
        table_layout = QVBoxLayout()
        table_layout.addWidget(parent.table_manager.stacked_widget)  # Изменение здесь
        table_widget = QWidget()
        table_widget.setLayout(table_layout)
        return table_widget

    def create_graph_widget(self):
        # Создание нового объекта Figure для хранения графика
        figure = Figure()
        #figure.set_size_inches(10, 5, forward=True)

        # Создание объекта FigureCanvas для отображения графика
        canvas = FigureCanvas(figure)

        # Создание layout для размещения холста с графиком
        graph_layout = QVBoxLayout()
        graph_layout.addWidget(canvas)

        # Создание виджета для хранения layout
        graph_widget = QWidget()
        graph_widget.setLayout(graph_layout)

        # Возврат виджета, холста и фигуры, чтобы их можно было использовать в других частях кода
        return graph_widget, canvas, figure

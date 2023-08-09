from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QComboBox, QLabel, QSplitter, QTabWidget, QTextEdit
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QTextCursor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class UIInitializer(QWidget):
    def __init__(self, parent, viewer):
        super().__init__(parent)
        self.parent = parent
        self.viewer = viewer

        # Установка минимального размера окна
        self.setMinimumSize(QSize(1220, 920))  

        # Создание элементов
        self.create_buttons()
        self.create_combo_boxes()
        buttons_widget = self.create_buttons_layout()

        # Создание вкладок
        tab_widget = self.create_tab_widget()

        # Инициализация консоли
        self.console_widget = self.create_console_widget()

        # Создание главного разделителя
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(buttons_widget)
        main_splitter.addWidget(tab_widget)
        main_splitter.addWidget(self.console_widget)  # добавляем консоль справа

        # Установка размеров областей
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 7)
        main_splitter.setStretchFactor(2, 4)  # консоль занимает 1/5 часть справа

        # Добавление разделителей на главный layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(main_splitter)

        # Установка главного layout
        self.setLayout(main_layout)

    def create_console_widget(self):
        # Создание консоли для вывода логов
        console_widget = QTextEdit()
        console_widget.setReadOnly(True)
        handler = QTextEditLogger(console_widget)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return console_widget

    def console_log_stream(self):
        while True:
            yield self.console_log_write
    
    def console_log_write(self, text):
        self.console_widget.moveCursor(QTextCursor.End)
        self.console_widget.insertPlainText(text)
        
    def create_buttons(self):
        self.button_load_csv = self.create_button('Load CSV', self.parent.load_csv_table)
        self.button_export_csv = self.create_button('Export CSV', self.viewer.export_csv)
        self.button_compute_peaks = self.create_button('Compute peaks', self.parent.compute_peaks)
        self.button_interactive = self.create_button('Interactive Mode', self.parent.switch_to_interactive_mode, checkable=True)
        self.button_add_diff = self.create_button('Add Diff', self.parent.add_diff)
        self.button_options_mode = self.create_button('Options Mode', self.parent.options_mode)
        logger.debug("Кнопки созданы.")
        
    def create_combo_boxes(self):
        self.combo_box_x = QComboBox()
        self.combo_box_x.addItem("Select X")
        self.combo_box_y = QComboBox()
        self.combo_box_y.addItem("Select Y")
        
        self.combo_box_x.currentIndexChanged.connect(self.parent.plot_graph)
        self.combo_box_y.currentIndexChanged.connect(self.parent.plot_graph)

    def create_buttons_layout(self):
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(self.button_load_csv)
        buttons_layout.addWidget(self.button_export_csv)
        buttons_layout.addWidget(self.button_options_mode)     
        buttons_layout.addWidget(self.button_compute_peaks)
        buttons_layout.addWidget(self.button_interactive)
        buttons_layout.addWidget(self.button_add_diff)
        buttons_layout.addWidget(self.combo_box_x)
        buttons_layout.addWidget(self.combo_box_y)
        
        buttons_layout.addStretch(1) # Добавление растяжимости

        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)
        logger.debug(f"Контейнер кнопок создан с размером: {buttons_widget.size()}")
        return buttons_widget

    def create_button(self, text, action, checkable=False):
        button = QPushButton(text, self)
        button.clicked.connect(action)
        if checkable:
            button.setCheckable(True)
        return button

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
        graph_layout.addStretch(1)
        
        # Создание виджета для хранения layout
        graph_widget = QWidget()
        graph_widget.setLayout(graph_layout)

        # Возврат виджета, холста и фигуры, чтобы их можно было использовать в других частях кода
        return graph_widget, canvas, figure

    def create_tab_widget(self):
        # Создание вкладок
        tab_widget = QTabWidget()

        # Создание блока с таблицей
        table_widget1 = self.create_table_widget1(self.parent)

        # Создание блока с графиком для вкладки 1,2
        graph_widget1, self.canvas1, self.figure1 = self.create_graph_widget()
        graph_widget2, self.canvas2, self.figure2 = self.create_graph_widget()

        # Вкладка 1: оси, таблица и консоль в столбец
        splitter_vertical1 = QSplitter(Qt.Vertical)
        splitter_vertical1.addWidget(table_widget1)
        splitter_vertical1.addWidget(graph_widget1)

        # Установка начальных размеров областей (пример)
        splitter_vertical1.setSizes([400, 600])

        # Установка коэффициентов растяжения (пример)
        splitter_vertical1.setStretchFactor(0, 1)
        splitter_vertical1.setStretchFactor(1, 2)

        # Вкладка 2: только оси
        # Вкладка 3: только таблица (может потребоваться дальнейшая настройка)
        table_widget3 = None

        # Добавление вкладок в widget вкладок
        tab_widget.addTab(splitter_vertical1, "Axes & Table")
        tab_widget.addTab(graph_widget2, "Axes Only")
        tab_widget.addTab(table_widget3, "Table Only")

        return tab_widget
    
    def resizeEvent(self, event):
        logger.debug(f"Окно приложения изменило размер на {event.size()}")
        super(UIInitializer, self).resizeEvent(event)
        
class QTextEditLogger(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        msg = self.format(record)
        self.widget.moveCursor(QTextCursor.End)
        self.widget.insertPlainText(msg + '\n')

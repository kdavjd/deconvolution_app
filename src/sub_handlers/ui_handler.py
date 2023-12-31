from PyQt5.QtCore import QObject, Qt, QModelIndex
from PyQt5.QtWidgets import QApplication, QInputDialog, QLineEdit, QDialog, QVBoxLayout, QCheckBox, QPushButton
from .graph_handler import GraphHandler


class UIHandler(QObject):
    """
    Обработчик пользовательского интерфейса.

    Attributes:
        main_app: Ссылка на главное приложение.
        ui_initializer: Компонент для инициализации пользовательского интерфейса.
        table_manager: Менеджер для управления данными в таблицах.
        viewer: Компонент для просмотра данных.
        graph_handler: Обработчик для управления графиками.

    Methods:
        connect_signals(): Подключает сигналы к слотам.
        handle_table_clicked(q_model_index): Обрабатывает клики по таблице.
        connect_canvas_events(): Подключает события к холсту.
        disconnect_canvas_events(): Отключает события от холста.
    """

    def __init__(self, main_app):
        """
        Инициализация обработчика UI.

        Args:
            main_app: Ссылка на главное приложение.
        """
        super().__init__()
        self.main_app = main_app
        self.ui_initializer = main_app.ui_initializer
        self.table_manager = main_app.table_manager
        self.viewer = main_app.viewer
        self.graph_handler = GraphHandler(main_app)

    def connect_signals(self):
        """
        Подключение сигналов от таблиц к соответствующему слоту обработки.
        """
        self.table_manager.tables['gauss'].clicked.connect(self.handle_table_clicked)
        self.table_manager.tables['options'].clicked.connect(self.handle_table_clicked)
        if self.viewer.file_name:
            self.table_manager.tables[self.viewer.file_name].clicked.connect(self.handle_table_clicked)

    def handle_table_clicked(self, q_model_index: QModelIndex):
        """
        Обработка клика по таблице.

        Args:
            q_model_index (QModelIndex): Индекс элемента в модели данных.
        """
        table = self.table_manager.tables[self.table_manager.current_table_name]
        model = table.model()

        # Если нажата клавиша Control, удаляем строку и перестраиваем графики.
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            self.table_manager.delete_row(q_model_index.row())
            self.graph_handler.rebuild_gaussians()
        # Если нажата клавиша Alt, удаляем столбец.
        elif QApplication.keyboardModifiers() == Qt.AltModifier:
            self.table_manager.delete_column(q_model_index.column())
        # Если нажата клавиша Shift
        elif QApplication.keyboardModifiers() == Qt.ShiftModifier:            
            self.graph_handler.rebuild_gaussians_signal.emit()        
            
        else:
            pass

    def connect_canvas_events(self):
        """
        Подключает обработчики событий к холсту графика.
        """
        self.table_manager.fill_table('gauss')       
        # Подключение событий нажатия и отпускания кнопки мыши к методам обработчика графов.
        self.press_cid = self.ui_initializer.canvas1.mpl_connect('button_press_event', self.graph_handler.on_press)
        self.release_cid = self.ui_initializer.canvas1.mpl_connect('button_release_event', self.graph_handler.on_release)

    def disconnect_canvas_events(self):
        """
        Отключает обработчики событий от холста графика.
        """
        self.table_manager.fill_table(self.viewer.file_name)        
        # Отключение событий нажатия и отпускания кнопки мыши.
        self.ui_initializer.canvas1.mpl_disconnect(self.press_cid)
        self.ui_initializer.canvas1.mpl_disconnect(self.release_cid)
        # Перестроение гауссиан.
        self.graph_handler.rebuild_gaussians()       
    

    def get_selected_peak_types(self):
        dialog = QDialog()
        dialog.setWindowTitle("Выбор типов пиков")
        layout = QVBoxLayout()

        checkboxes = {}
        for peak_type in ['gauss', 'fraser', 'ads']:
            checkbox = QCheckBox(peak_type)
            checkbox.setChecked(True)
            layout.addWidget(checkbox)
            checkboxes[peak_type] = checkbox

        btn = QPushButton("Применить")
        layout.addWidget(btn)
        btn.clicked.connect(dialog.accept)

        dialog.setLayout(layout)

        if dialog.exec_():
            selected_types = [key for key, checkbox in checkboxes.items() if checkbox.isChecked()]
            return selected_types
        else:
            return None

from PyQt5.QtWidgets import QApplication, QLineEdit, QInputDialog, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphHandler(QObject):
    """
    Обработчик графиков для интерактивного рисования и анализа данных.

    Атрибуты:
        main_app: Ссылка на главное приложение.
        ui_initializer: Инициализатор пользовательского интерфейса.
        math_operations: Объект для математических операций.
        viewer: Объект для просмотра данных.
        table_manager: Управление таблицей данных.

    Методы:
        on_release(event: Qt Event): Обработка события отпускания кнопки мыши.
        on_press(event: Qt Event): Обработка события нажатия кнопки мыши.
        rebuild_gaussians(): Перестроение всех гауссовых кривых на графике.
        plot_graph(): Построение базового графика.

    """
    def __init__(self, main_app):
        """
        Инициализация обработчика графика.

        Args:
            main_app: Ссылка на главное приложение.
        """
        super().__init__()
        self.main_app = main_app
        # Инициализация основных компонентов главного приложения
        self.ui_initializer = main_app.ui_initializer
        self.math_operations = main_app.math_operations
        self.viewer = main_app.viewer
        self.table_manager = main_app.table_manager

    def on_release(self, event):
        """
        Обработка события отпускания кнопки мыши.

        Функция вызывается при отпускании кнопки мыши на графике.
        Задача - построить гауссову кривую на основе данных из таблицы.

        Args:
            event: Событие Qt.
        """
        release_x = event.xdata
        width = 2 * abs(release_x - self.press_x)
        # Получение данных из таблицы
        x_column_data = self.table_manager.get_column_data(self.viewer.file_name, self.ui_initializer.combo_box_x.currentText())
        x = np.linspace(min(x_column_data), max(x_column_data), 1000)
        y = self.math_operations.gaussian(x, self.press_y, self.press_x, width)

        # Построение графика
        ax = self.ui_initializer.figure1.get_axes()[0]
        ax.plot(x, y, 'r-')
        self.ui_initializer.canvas1.draw()
        
        # Добавление информации о гауссиане в таблицу
        self.table_manager.add_gaussian_to_table(self.press_y, self.press_x, width)

    def on_press(self, event):
        """
        Обработка события нажатия кнопки мыши.

        Запоминает позицию нажатия для дальнейших манипуляций.

        Args:
            event: Событие Qt.
        """
        self.press_x = event.xdata
        self.press_y = event.ydata

    def rebuild_gaussians(self):
        """
        Перестроение всех гауссовых кривых на графике.

        Пересоздает график, учитывая актуальные данные из таблицы.
        """
        self.plot_graph()  
        ax = self.ui_initializer.figure1.get_axes()[0]
        cumfunc = np.zeros(1000)
        for _, row in self.table_manager.data['gauss'].iterrows():
            x_column_data = self.table_manager.get_column_data(self.viewer.file_name, self.ui_initializer.combo_box_x.currentText()) 
            x = np.linspace(min(x_column_data), max(x_column_data), 1000)
            if row['type'] == 'gauss':
                y = self.math_operations.gaussian(x, row['height'], row['center'], row['width'])
            else:
                y = self.math_operations.fraser_suzuki(
                    x, float(row['height']), float(row['center']), float(row['width']), float(row['coeff_1']))
                _coef = str(row['coeff_1'])
                logger.info(f'В rebuild_gaussians коэффициент = {_coef}')
            ax.plot(x, y,)
            cumfunc += y
        ax.plot(x, cumfunc,)
        self.ui_initializer.canvas1.draw()

    def plot_graph(self):
        """
        Построение базового графика.

        Задача - отобразить данные из выпадающего списка столбцов таблицы на графике.
        """
        x_column = self.ui_initializer.combo_box_x.currentText() 
        y_column = self.ui_initializer.combo_box_y.currentText() 

        if not x_column or not y_column:  
            return

        self.ui_initializer.figure1.clear() 

        ax = self.ui_initializer.figure1.add_subplot(111) 
        ax.plot(self.viewer.df[x_column], self.viewer.df[y_column], 'b-')

        self.ui_initializer.canvas1.draw()

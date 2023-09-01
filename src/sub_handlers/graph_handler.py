from PyQt5.QtWidgets import QApplication, QLineEdit, QInputDialog, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np
from src.logger_config import logger

class GraphHandler(QObject):
    # Определение сигналов для каждого метода
    on_release_signal = pyqtSignal(object)
    on_press_signal = pyqtSignal(object)
    rebuild_gaussians_signal = pyqtSignal()
    plot_graph_signal = pyqtSignal()
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

        # Подключение сигналов к соответствующим слотам
        self.on_release_signal.connect(self.on_release)
        self.on_press_signal.connect(self.on_press)
        self.rebuild_gaussians_signal.connect(self.rebuild_gaussians)
        self.plot_graph_signal.connect(self.plot_graph)

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
                
        # Добавление информации о гауссиане в таблицу
        self.table_manager.add_gaussian_to_table_signal.emit(self.press_y, self.press_x, width)
        # Отрисовка гауссиан и кумулятивного графика
        self.rebuild_gaussians_signal.emit()

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
        
        if self.table_manager.data['gauss'].size == 0:
            return        
        
        ax = self.ui_initializer.figure1.get_axes()[0]
        cumfunc = np.zeros(1000)
        for _, row in self.table_manager.data['gauss'].iterrows():            
            x_column_data = self.table_manager.get_column_data(self.viewer.file_name, self.ui_initializer.combo_box_x.currentText()) 
            x = np.linspace(min(x_column_data), max(x_column_data), 1000)
            if row['type'] == 'gauss':
                y = self.math_operations.gaussian(x, row['height'], row['center'], row['width'])
            elif row['type'] == 'fraser':
                y = self.math_operations.fraser_suzuki(
                    x, float(row['height']), float(row['center']), float(row['width']), float(row['coeff_a']))
                _coef = str(row['coeff_a'])
                logger.debug(f'В rebuild_gaussians коэффициент = {_coef}')
            elif row['type'] == 'ads':
                y = self.math_operations.asymmetric_double_sigmoid(
                    x, float(row['height']), float(row['center']), float(row['width']), float(row['coeff_s1']), float(row['coeff_s2']))
                _coef1 = str(row['coeff_s1'])
                _coef2 = str(row['coeff_s2'])
                logger.debug(f'В rebuild_gaussians coeff_a = {_coef1}, coeff_2 = {_coef2}')
            else:
                y = self.math_operations.fraser_suzuki(
                    x, float(row['height']), float(row['center']), float(row['width']), float(row['coeff_a']))
                _coef = str(row['coeff_a'])
                logger.info(f'В rebuild_gaussians отработал else вместо fraser')
            
            ax.plot(x, y)
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

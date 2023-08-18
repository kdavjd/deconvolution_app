from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal
from .graph_handler import GraphHandler
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataHandler(QObject):
    """
    Класс для обработки данных и управления связанными действиями.

    Этот класс включает в себя методы для обработки гауссовой кривой, вычисления пиков, 
    обновления данных и других задач, связанных с обработкой данных.

    Attributes:
        main_app (object): Ссылка на главное приложение.
        viewer (object): Компонент для просмотра данных.
        table_manager (object): Менеджер для управления данными в таблицах.
        math_operations (object): Компонент для выполнения математических операций.
        ui_initializer (object): Компонент для инициализации пользовательского интерфейса.
        graph_handler (object): Обработчик для управления графиками.
    
    Methods:
        add_diff_button_pushed():
            Обрабатывает нажатие кнопки для добавления производной данных.
        
        get_init_params() -> list:
            Получает начальные параметры для гауссовой кривой.
        
        update_gaussian_data(best_params: list, best_combination: list, coeff_1: list[float]) -> DataFrame:
            Обновляет данные гауссовой кривой на основе оптимальных параметров.
        
        add_reaction_cummulative_func(best_params: list, best_combination: list, x_values: np.array, 
                                      y_column: str, cummulative_func: np.array):
            Добавляет кумулятивную функцию реакции на основе гауссовой кривой.
        
        compute_peaks_button_pushed(coeff_1: list[float], best_rmse: Optional[float] = None) -> float:
            Обрабатывает нажатие кнопки для вычисления пиков.
    """
    def __init__(self, main_app):
        """
        Инициализатор обработчика данных.

        Args:
            main_app (object): Ссылка на главное приложение.
        """
        super().__init__()
        self.main_app = main_app
        # Инициализация основных компонентов главного приложения
        self.viewer = main_app.viewer
        self.table_manager = main_app.table_manager
        self.math_operations = main_app.math_operations
        self.ui_initializer = main_app.ui_initializer
        self.graph_handler = GraphHandler(main_app)

    def add_diff_button_pushed(self):
        """
        Обработчик кнопки для добавления производной данных.

        Вычисляет производную по выбранным столбцам таблицы и добавляет результат как новый столбец.
        """
        # Получение имен выбранных столбцов
        x_column_name = self.ui_initializer.combo_box_x.currentText()
        y_column_name = self.ui_initializer.combo_box_y.currentText()

        # Вычисление производной
        dy_dx = self.math_operations.compute_derivative(
            self.viewer.df[x_column_name],
            self.viewer.df[y_column_name])

        # Добавление нового столбца с производной в DataFrame
        new_column_name = y_column_name + '_diff'
        self.viewer.df[new_column_name] = dy_dx

        # Обновление интерфейса: заполнение таблицы и комбо-боксов
        self.table_manager.fill_table(self.viewer.file_name)
        self.table_manager.fill_combo_boxes(
            self.ui_initializer.combo_box_x,
            self.ui_initializer.combo_box_y) 

        # Установка нового столбца как текущего для Y в комбо-боксе
        self.ui_initializer.combo_box_y.setCurrentText(new_column_name)

    def get_init_params(self):
        """
        Получение начальных параметров для гауссовой кривой.

        Returns:
            list: Список начальных параметров.
        """
        logger.debug("Начало метода get_init_params.")        
        init_params = []
        for index, row in self.table_manager.data['gauss'].iterrows():
            logger.debug(f"Обработка строки {index}: height={row['height']}, center={row['center']}, width={row['width']}")
            init_params.extend([row['height'], row['center'], row['width']])
        logger.debug(f"Длина начальных параметров: {len(init_params)}")
        logger.debug(f"Конец метода get_init_params. Полученные параметры: {str(init_params)}.")
        return init_params
    
    def update_gaussian_data(self, best_params, best_combination, coeff_1):
        """
        Обновление данных гауссовой кривой на основе оптимальных параметров.

        Args:
            best_params (list): Лучшие параметры гауссовой кривой.
            best_combination (list): Лучшая комбинация типов пиков.
            coeff_1 (list[float]): Список коэффициентов.

        Returns:
            DataFrame: Обновленные данные гауссовой кривой.
        """
        logger.debug("Начало метода update_gaussian_data.")
        gaussian_data = self.table_manager.data['gauss'].copy()

        for i, peak_type in enumerate(best_combination):
            height = best_params[3 * i]
            center = best_params[3 * i + 1]
            width = best_params[3 * i + 2]
            coeff_ = coeff_1[i]

            gaussian_data.at[i, 'height'] = height
            gaussian_data.at[i, 'center'] = center
            gaussian_data.at[i, 'width'] = width
            gaussian_data.at[i, 'type'] = peak_type
            gaussian_data.at[i, 'coeff_1'] = coeff_

        return gaussian_data

    def add_reaction_cummulative_func(self, best_params, best_combination, x_values, y_column, cummulative_func):
        """
        Добавление кумулятивной функции реакции на основе гауссовой кривой.

        Args:
            best_params (list): Лучшие параметры гауссовой кривой.
            best_combination (list): Лучшая комбинация типов пиков.
            x_values (np.array): Значения X для расчета функции.
            y_column (str): Имя столбца Y.
            cummulative_func (np.array): Кумулятивная функция.
        """
        logger.debug("Начало метода add_reaction_cummulative_func.")
        for i, peak_type in enumerate(best_combination):
            height = best_params[3 * i]
            center = best_params[3 * i + 1]
            width = best_params[3 * i + 2]  
            
            new_column_name = y_column + '_reaction_' + str(i)
            if peak_type == 'gauss':
                peak_func = self.math_operations.gaussian(x_values, height, center, width)
            else:
                peak_func = self.math_operations.fraser_suzuki(
                    x_values, height, center, width, 
                    float(self.table_manager.data['options']['coeff_1'].values))
                
            self.viewer.df[new_column_name] = peak_func
            cummulative_func += peak_func

        new_column_name = y_column + '_cummulative'
        self.viewer.df[new_column_name] = cummulative_func
        logger.debug("Конец метода add_reaction_cummulative_func.")

    def compute_peaks_button_pushed(self, coeff_1: list[float], best_rmse=None):
        """
        Обработчик кнопки для вычисления пиков.

        Args:
            coeff_1 (list[float]): Список коэффициентов.
            best_rmse (float, optional): Лучшее значение RMSE. Если не указано, будет вычислено.

        Returns:
            float: Лучшее значение RMSE.
        """
        coefficients_str = ', '.join(map(str, coeff_1))
        self.ui_initializer.console_widget.append(f'Получены коэффициенты: {coefficients_str}')        

        logger.info(f'Получены коэффициенты: {str(coeff_1)}')
        x_column_name = self.ui_initializer.combo_box_x.currentText() 
        y_column_name = self.ui_initializer.combo_box_y.currentText() 
        init_params = self.get_init_params()
        x_values = self.table_manager.get_column_data(x_column_name)
        y_values = self.table_manager.get_column_data(y_column_name)

        maxfev = int(self.table_manager.data['options']['maxfev'].values)        
        num_peaks = len(init_params) // 3
        if best_rmse is None:
            best_params, best_combination, best_rmse = self.math_operations.compute_best_peaks(
                x_values, y_values, num_peaks, init_params, maxfev, coeff_1)  
            
        best_gaussian_data = self.update_gaussian_data(best_params, best_combination, coeff_1)
        self.table_manager.update_table_data('gauss', best_gaussian_data)
        
        self.main_app.ui_initializer.console_widget.append(f'Лучшее RMSE: {best_rmse:.5f}')
        self.main_app.ui_initializer.console_widget.append(f'Лучшая комбинация пиков: {best_combination}')
        QApplication.processEvents()
        
        cummulative_func = np.zeros(len(x_values)) 
        self.add_reaction_cummulative_func(best_params, best_combination, x_values, y_column_name, cummulative_func)
        
        self.table_manager.data['options']['rmse'] = best_rmse                              
        
        self.graph_handler.rebuild_gaussians()
        
        self.table_manager.fill_table('gauss')
        
        return best_rmse
    
    
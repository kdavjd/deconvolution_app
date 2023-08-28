from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
from scipy.optimize import curve_fit
from itertools import product
import threading
from typing import Tuple
from src.logger_config import logger



class ComputeCombinationThread(QThread):
    
    def __init__(self, x_values, y_values, combination, initial_params, maxfev, bounds, coeff_1, results_dict, lock, console_message_signal):
        super().__init__()
        self.x_values = x_values
        self.y_values = y_values
        self.combination = combination
        self.initial_params = initial_params
        self.maxfev = maxfev
        self.bounds = bounds
        self.coeff_1 = coeff_1
        self.results_dict = results_dict
        self.lock = lock
        self.result = None
        self.console_message_signal = console_message_signal

    def run(self):
        try:
            logger.debug(f"Запуск потока для комбинации {self.combination}.")

            def fit_function(x, *params):
                return MathOperations.peaks(x, self.combination, self.coeff_1, *params)

            popt, _ = curve_fit(fit_function, self.x_values, self.y_values, p0=self.initial_params, maxfev=self.maxfev, bounds=self.bounds, method='trf')
            predicted = MathOperations.peaks(self.x_values, self.combination, self.coeff_1, *popt)
            rmse = np.sqrt(np.mean((self.y_values - predicted) ** 2))
            self.result = (self.combination, popt, rmse)
            
            with self.lock:
                if self.result:
                    logger.info(f"Комбинация: {self.combination}\n RMSE: {np.round(rmse, 4)}")
                    self.console_message_signal.emit(f"Комбинация: {self.combination}\n RMSE: {np.round(rmse, 4)}")
                    self.results_dict[self.combination] = {'popt': self.result[1], 'rmse': self.result[2]}
                else:
                    logger.warning(f"Результат не найден для комбинации:\n {self.combination}")
                logger.debug(f"Поток для комбинации: {self.combination} завершился успешно.")
                
        except RuntimeError:
            logger.exception(f"Не удалось подобрать комбинацию:\n {self.combination}")
        except Exception as e:
            logger.exception(f"Неожиданное исключение в потоке для комбинации:\n {self.combination}: {str(e)}")
         

class MathOperations:
    
    @staticmethod
    def handle_thread_finished(combination, array_data, float_value, results_dict):
        logger.debug("Начало исполнения handle_thread_finished")
        if combination:
            logger.debug(f"Добавление результатов для комбинации {combination} в results")
            results_dict.update({combination: {'popt': array_data, 'rmse': float_value}})
        else:
            logger.warning(f"Получен пустой результат в handle_thread_finished")    

    @staticmethod
    def gaussian(x: np.ndarray, a0: float, a1: float, a2: float) -> np.ndarray:
        """Гауссовская функция."""
        a0, a1, a2 = max(0, float(a0)), float(a1), float(a2)
        return a0 * np.exp(-((x - a1) ** 2) / (2 * a2 ** 2))

    @staticmethod
    def compute_derivative(x_values: np.ndarray, y_values: np.ndarray) -> np.ndarray:
        dy_dx = np.gradient(y_values, x_values) * -1
        return dy_dx

    @staticmethod
    def fraser_suzuki(x: np.array, a0: float, a1: float, a2: float, a3: float) -> np.array:
        with np.errstate(divide='ignore', invalid='ignore'):
            result = a0 * np.exp(-np.log(2)*((np.log(1+2*a3*((x-a1)/a2))/a3)**2))
        result = np.nan_to_num(result, nan=0)
        return result

    @staticmethod
    def peaks(x: np.array, peak_types: list, coeff_1: list, *params: float) -> np.array:
        y = np.zeros_like(x)
        for i, peak_type in enumerate(peak_types):
            a0 = params[3*i]
            a1 = params[3*i+1]
            a2 = params[3*i+2]
            if peak_type == 'gauss':
                y = y + MathOperations.gaussian(x, a0, a1, a2)
            else: 
                y = y + MathOperations.fraser_suzuki(x, a0, a1, a2, coeff_1[i]) 
        return y

    @staticmethod
    def compute_best_peaks(
        x_values: np.array, y_values: np.array, num_peaks: int, 
        initial_params: list, maxfev: int, coeff_1: list, 
        console_message_signal: pyqtSignal
        ) -> Tuple[np.array, Tuple[str, ...], float]:
        
        logger.info("\nНачало деконволюции пиков.\n")
        logger.debug(f"Полученные начальные параметры:\n\n {str(initial_params)}, \n\nкол-во пиков: {num_peaks}")
        
        peak_types = ['gauss', 'fraser']
        combinations = list(product(peak_types, repeat=num_peaks))
        
        best_rmse = np.inf
        best_popt = None
        best_combination = None

        lower_bounds = [0] * num_peaks * 3
        upper_bounds = [np.inf] * num_peaks * 3

        bounds = (lower_bounds, upper_bounds)
        
        results_dict = {}  # Пустой словарь для результатов
        lock = threading.Lock()
        threads = []
        
        for combination in combinations:
            thread = ComputeCombinationThread(
                x_values, y_values, combination, initial_params, 
                maxfev, bounds, coeff_1, results_dict, lock, console_message_signal)
            thread.start()
            threads.append(thread)
        
        # Ожидание завершения всех потоков
        for thread in threads:
            thread.wait()

        if not results_dict:
            logger.error("Не удалось найти подходящую комбинацию. Все потоки завершились ошибками.")
            return None, None, None
        
        # Нахождение лучшей комбинации
        best_combination = min(results_dict, key=lambda k: results_dict[k]['rmse'])
        best_popt = results_dict[best_combination]['popt']
        best_rmse = results_dict[best_combination]['rmse']

        logger.info(f"Лучшая комбинация:\n {best_combination}\n с RMSE: {np.round(best_rmse, 4)}")
        logger.debug("Конец метода compute_best_peaks.")
        
        return best_popt, best_combination, best_rmse
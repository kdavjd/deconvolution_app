from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

import threading
from typing import Tuple
from src.logger_config import logger


class ComputeCombinationThread(QThread):
    
    def __init__(self, x_values, y_values, combination, initial_params, maxfev, bounds, coeff_1, s1, s2, results_dict, lock, console_message_signal):
        super().__init__()
        self.x_values = x_values
        self.y_values = y_values
        self.combination = combination
        self.initial_params = initial_params
        self.maxfev = maxfev
        self.bounds = bounds
        self.coeff_1 = coeff_1
        self.s1 = s1 
        self.s2 = s2
        self.results_dict = results_dict
        self.lock = lock
        self.result = None
        self.console_message_signal = console_message_signal

    def run(self):
        try:
            logger.debug(f"Запуск потока для комбинации {self.combination}.")

            def fit_function(x, *params):
                return MathOperations.peaks(x, self.combination, self.coeff_1, self.s1, self.s2, *params)

            popt, _ = curve_fit(fit_function, self.x_values, self.y_values, p0=self.initial_params, maxfev=self.maxfev, bounds=self.bounds, method='trf')
            predicted = MathOperations.peaks(self.x_values, self.combination, self.coeff_1, self.s1, self.s2, *popt)
            rmse = np.sqrt(np.mean((self.y_values - predicted) ** 2))
            self.result = (self.combination, popt, rmse)
            
            with self.lock:
                if self.result:
                    logger.info(f"Комбинация: {self.combination} RMSE: {np.round(rmse, 5)}")
                    self.console_message_signal.emit(f"Комбинация: {self.combination}\n RMSE: {np.round(rmse, 4)}")
                    self.results_dict[self.combination] = {'popt': self.result[1], 'rmse': self.result[2]}
                else:
                    logger.warning(f"Результат не найден для комбинации:\n {self.combination}")
                logger.debug(f"Поток для комбинации: {self.combination} завершился успешно.")
                
        except RuntimeError:
            logger.exception(f"Не удалось подобрать комбинацию:\n {self.combination}")
            self.console_message_signal.emit(f"Не удалось подобрать комбинацию:\n {self.combination}\n \
                                             Попробуйте увеличить maxvef в options.\n \
                                             или пересмотрите ограничения на форму пиков.")
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
    def gaussian(x: np.ndarray, h: float, z: float, w: float) -> np.ndarray:        
        return h * np.exp(-((x - z) ** 2) / (2 * w ** 2))

    @staticmethod
    def compute_derivative(x_values: np.ndarray, y_values: np.ndarray) -> np.ndarray:
        dy_dx = np.gradient(y_values, x_values) * -1
        return dy_dx

    @staticmethod
    def fraser_suzuki(x: np.array, h: float, z: float, w: float, a3: float) -> np.array:        
        with np.errstate(divide='ignore', invalid='ignore'):
            result = h * np.exp(-np.log(2)*((np.log(1+2*a3*((x-z)/w))/a3)**2))
        result = np.nan_to_num(result, nan=0)
        return result
    
    @staticmethod
    def asymmetric_double_sigmoid(x: np.array, h: float, z: float, w: float, s1: float, s2: float) -> np.array:
        # Ограничиваем значения массива x, чтобы избежать переполнения при использовании np.exp()
        safe_x = np.clip(x, -709, 709)
        
        # Вычисляем аргумент для экспоненты для term1
        exp_arg = -((safe_x - z + w/2) / s1)
        # Ограничиваем значение аргумента экспоненты, чтобы избежать переполнения
        clipped_exp_arg = np.clip(exp_arg, -709, 709)
        
        # Вычисляем первое сигмоидное слагаемое
        term1 = 1 / (1 + np.exp(clipped_exp_arg))
        
        # Вычисляем внутренний член для второго сигмоидного слагаемого
        inner_term = 1 / (1 + np.exp(-((safe_x - z - w/2) / s2)))
        # Вычисляем второе сигмоидное слагаемое
        term2 = 1 - inner_term
        
        # Возвращаем итоговый результат: произведение константы h и двух сигмоидных слагаемых
        result = h * term1 * term2
        return result

    @staticmethod
    def peaks(x: np.array, peak_types: list, coeff_1: list, s1: list, s2: list, *params: float) -> np.array:
        y = np.zeros_like(x)
        for i, peak_type in enumerate(peak_types):
            h = params[3*i]
            z = params[3*i+1]
            w = params[3*i+2]
            if peak_type == 'gauss':
                y = y + MathOperations.gaussian(x, h, z, w)
            elif peak_type == 'fraser': 
                y = y + MathOperations.fraser_suzuki(x, h, z, w, coeff_1[i])
            elif peak_type == 'ads':
                y = y + MathOperations.asymmetric_double_sigmoid(x, h, z, w, s1[i], s2[i])

        return y

    @staticmethod
    def compute_best_peaks(
        x_values: np.array, y_values: np.array, 
        peaks_params: list[float], maxfev: int, coeff_1: list[float], s1: list[float], s2: list[float],
        combinations: list[str], peaks_bounds: list[tuple[float, float]],
        console_message_signal: pyqtSignal
        ) -> Tuple[np.array, Tuple[str, ...], float]:
        
        logger.info("Начало деконволюции пиков.")
        logger.debug(f"Полученные начальные параметры: {peaks_params}")
        
        best_rmse = np.inf
        best_popt = None
        best_combination = None
        
        results_dict = {}  # Пустой словарь для результатов
        lock = threading.Lock()
        threads = []
        
        for combination in combinations:
            thread = ComputeCombinationThread(
                x_values, y_values, combination, peaks_params, 
                maxfev, peaks_bounds, coeff_1, s1, s2, results_dict, lock, console_message_signal)
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

        logger.info(f"Лучшая комбинация: {best_combination} RMSE: {np.round(best_rmse, 4)}")
        logger.debug("Конец метода compute_best_peaks.")
        
        return best_popt, best_combination, best_rmse
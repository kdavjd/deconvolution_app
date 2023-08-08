import numpy as np
from scipy.optimize import curve_fit
from itertools import product
import logging

logging.basicConfig(level=logging.info)
logger = logging.getLogger(__name__)

class MathOperations:

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
        x_values: np.array, y_values: np.array, num_peaks: int, initial_params: list, maxfev: int, coeff_1: list):
        
        logger.debug("Начало вычисления лучших пиков.")
        logger.debug(f"Полученные начальные параметры: {str(initial_params)}, кол-во пиков: {num_peaks}")
        
        peak_types = ['gauss', 'fraser']
        
        combinations = list(product(peak_types, repeat=num_peaks))
        logger.debug(f"Комбинации: {combinations}")
        
        best_rmse = np.inf
        best_popt = None
        best_combination = None

        lower_bounds = [0] * num_peaks * 3
        upper_bounds = [np.inf] * num_peaks * 3

        bounds = (lower_bounds, upper_bounds)
        
        for combination in combinations:
            try:
                logger.debug(f"Пытаемся подобрать комбинацию: {combination}")
                
                def fit_function(x, *params):
                    return MathOperations.peaks(x, combination, coeff_1, *params)
                
                popt, pcov = curve_fit(
                    fit_function, x_values, y_values, p0=initial_params, maxfev=maxfev, bounds=bounds, method='trf')                

                logger.debug(f"Результат popt из curve_fit: {popt}")
                logger.debug(f"Длина popt: {len(popt)}")
                
                predicted = MathOperations.peaks(x_values, combination, coeff_1, *popt)

                rmse = np.sqrt(np.mean((y_values - predicted)**2))
                logger.debug(f"Комбинация: {combination} достигла RMSE: {rmse}")

                if rmse < best_rmse:
                    best_rmse = rmse
                    best_popt = popt
                    best_combination = combination
            except RuntimeError:
                logger.warning(f"Не удалось подобрать комбинацию: {combination}")

        logger.info(f"Лучшая комбинация: {best_combination} с RMSE: {best_rmse}")
        logger.debug("Конец метода compute_best_peaks.")
        return best_popt, best_combination, best_rmse
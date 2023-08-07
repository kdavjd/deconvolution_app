import numpy as np
from scipy.optimize import curve_fit
from itertools import product
import logging

logging.basicConfig(level=logging.info)
logger = logging.getLogger(__name__)

class MathOperations:

    @staticmethod
    def gaussian(x, a0, a1, a2):
        """Гауссовская функция."""
        a0, a1, a2 = max(0, float(a0)), float(a1), float(a2)
        return a0 * np.exp(-((x - a1) ** 2) / (2 * a2 ** 2))


    @staticmethod
    def compute_derivative(x_values, y_values):
        dy_dx = np.gradient(y_values, x_values) * -1
        return dy_dx

    @staticmethod
    def fraser_suzuki(x, a0, a1, a2, a3):
        with np.errstate(divide='ignore', invalid='ignore'):
            result = a0 * np.exp(-np.log(2)*((np.log(1+2*a3*((x-a1)/a2))/a3)**2))
        result = np.nan_to_num(result, nan=0)
        return result

    @staticmethod
    def peaks(x, peak_types, coeff_1, *params):
        logger.debug(f"Длина params в функции peaks: {len(params)}")     
        y = np.zeros_like(x)
        for i, peak_type in enumerate(peak_types):
            a0 = params[3*i]
            a1 = params[3*i+1]
            a2 = params[3*i+2]
            logger.debug(f"Текущий индекс: {i}, параметры: {params[3*i]}, {params[3*i+1]}, {params[3*i+2]}")                       
            if peak_type == 'gauss':
                y = y + MathOperations.gaussian(x, a0, a1, a2)
            else: 
                y = y + MathOperations.fraser_suzuki(x, a0, a1, a2, coeff_1) 
        return y

    @staticmethod
    def compute_best_peaks(x_values, y_values, initial_params, maxfev, coeff_1):
        logger.debug("Начало вычисления лучших пиков.")
        logger.debug(f"Полученные начальные параметры: {str(initial_params)}")     
        peak_types = ['gauss', 'fraser']
        
        combinations = list(product(peak_types, repeat=len(initial_params)//3))
        logger.info(f"Комбинации: {combinations}")    
        best_rmse = np.inf
        best_popt = None
        best_combination = None

        lower_bounds = []
        upper_bounds = []
        
        for _ in range(len(initial_params)//3):
            lower_bounds.extend([0, 0, 0])  # Нижняя граница для первых трёх параметров из четырёх
            upper_bounds.extend([np.inf, np.inf, np.inf]) 
        
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
                logger.info(f"Комбинация: {combination} достигла RMSE: {rmse}")

                if rmse < best_rmse:
                    best_rmse = rmse
                    best_popt = popt
                    best_combination = combination
            except RuntimeError:
                logger.warning(f"Не удалось подобрать комбинацию: {combination}")

        logger.info(f"Лучшая комбинация: {best_combination} с RMSE: {best_rmse}")
        logger.debug("Конец метода compute_best_peaks.")
        return best_popt, best_combination, best_rmse
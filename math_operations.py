import numpy as np

class MathOperations:

    @staticmethod
    def gaussian(x, a0, a1, a2):
        """Гауссовская функция."""
        return a0 * np.exp(-((x - a1) ** 2) / (2 * a2 ** 2))

    @staticmethod
    def compute_derivative(x_values, y_values):
        """
        Функция вычисляет производную y по x используя np.gradient().

        Параметры:
        x_values : ndarray
            Массив данных для оси x.
        y_values : ndarray
            Массив данных для оси y.

        Возвращает:
        dy_dx : ndarray
            Массив с вычисленными значениями производной.
        """
        # Рассчитываем производную y по x с помощью np.gradient()
        dy_dx = np.gradient(y_values, x_values) * -1

        return dy_dx

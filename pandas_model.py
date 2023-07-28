from PyQt5.QtCore import Qt, QAbstractTableModel

class PandasModel(QAbstractTableModel):
    """
    Класс PandasModel, наследующий от QAbstractTableModel. Используется для взаимодействия 
    между pandas DataFrame и QTableView.
    """

    def __init__(self, data, parent=None):
        """
        Инициализатор класса.

        :param data: pandas DataFrame, который будет отображаться.
        :param parent: родительский виджет.
        """
        QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        """
        Возвращает количество строк в DataFrame.

        :param parent: родительский индекс (не используется, оставлен для совместимости).
        :return: число строк.
        """
        return self._data.shape[0]

    def columnCount(self, parent=None):
        """
        Возвращает количество столбцов в DataFrame.

        :param parent: родительский индекс (не используется, оставлен для совместимости).
        :return: число столбцов.
        """
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        """
        Возвращает данные для отображения в таблице.

        :param index: индекс ячейки.
        :param role: роль данных.
        :return: данные для отображения в ячейке или None, если ячейка недействительна.
        """
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        """
        Возвращает заголовки для строк и столбцов.

        :param col: индекс столбца.
        :param orientation: ориентация заголовка (вертикальная или горизонтальная).
        :param role: роль данных.
        :return: заголовок столбца или None, если заголовок недействителен.
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None

    def setData(self, index, value, role):
        """
        Позволяет изменить данные в DataFrame.

        :param index: индекс ячейки.
        :param value: новое значение.
        :param role: роль данных.
        :return: True, если данные были успешно изменены, иначе False.
        """
        if index.isValid():
            if role == Qt.EditRole:
                row = index.row()
                if 0 <= row < self._data.shape[0]:
                    column = index.column()
                    self._data.iat[row, column] = value
                    return True
        return False

    def flags(self, index):
        """
        Определяет возможности ячейки.

        :param index: индекс ячейки.
        :return: набор флагов, определяющих возможности ячейки.
        """
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

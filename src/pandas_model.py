from PyQt5.QtCore import Qt, QAbstractTableModel, pyqtSignal


class PandasModel(QAbstractTableModel):
    """
    Класс для взаимодействия между pandas DataFrame и QTableView.

    Attributes:
        data_changed_signal (pyqtSignal): Сигнал изменения данных.
    """
    
    data_changed_signal = pyqtSignal()

    def __init__(self, data, parent=None):
        """
        Инициализация класса.

        Args:
            data (DataFrame): pandas DataFrame для отображения.
            parent (QWidget, optional): родительский виджет.
        """
        QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        """
        Возвращает количество строк в DataFrame.

        Args:
            parent (QModelIndex, optional): родительский индекс (не используется).

        Returns:
            int: число строк.
        """
        return self._data.shape[0]

    def columnCount(self, parent=None):
        """
        Возвращает количество столбцов в DataFrame.

        Args:
            parent (QModelIndex, optional): родительский индекс (не используется).

        Returns:
            int: число столбцов.
        """
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        """
        Возвращает данные для отображения в таблице.

        Args:
            index (QModelIndex): индекс ячейки.
            role (Qt.ItemDataRole, optional): роль данных.

        Returns:
            QVariant: данные для отображения или None, если ячейка недействительна.
        """
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Возвращает данные заголовка.

        Args:
            section (int): номер раздела (столбца или строки).
            orientation (Qt.Orientation): ориентация заголовка (горизонтальная или вертикальная).
            role (Qt.ItemDataRole, optional): роль данных.

        Returns:
            QVariant: данные заголовка или None, если данные недоступны.
        """
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._data.columns[section]
        if orientation == Qt.Vertical:
            return self._data.index[section]

    def set_data(self, index, value, role=Qt.EditRole):
        """
        Изменяет данные в DataFrame.

        Args:
            index (QModelIndex): индекс ячейки.
            value (QVariant): новое значение.
            role (Qt.ItemDataRole, optional): роль данных.

        Returns:
            bool: True, если данные успешно изменены, иначе False.
        """
        row = index.row()
        col = index.column()

        if role == Qt.EditRole:
            self._data.iat[row, col] = value
            self.dataChanged.emit(index, index)
            return True
        return False
    
    def setData(self, index, value, role=Qt.EditRole):
        """
        Изменяет данные в DataFrame.

        Args:
            index (QModelIndex): индекс ячейки.
            value (QVariant): новое значение.
            role (Qt.ItemDataRole, optional): роль данных.

        Returns:
            bool: True, если данные успешно изменены, иначе False.
        """
        row = index.row()
        col = index.column()

        if role == Qt.EditRole:
            value = str(value).replace(',', '.')
            self._data.iat[row, col] = value
            self.dataChanged.emit(index, index)
            self.data_changed_signal.emit()  # Ваши собственные сигналы могут быть здесь
            return True
        return False

    def flags(self, index):
        """
        Определяет возможности ячейки.

        Args:
            index (QModelIndex): индекс ячейки.

        Returns:
            Qt.ItemFlags: флаги, определяющие возможности ячейки.
        """
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

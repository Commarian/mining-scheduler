from PyQt5 import QtCore, QtWidgets


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, headers):
        super(TableModel, self).__init__()
        self._data = data
        self._headers = headers

    def data(self, index, role):
        value = self._data[index.row()][index.column()]

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return value
        elif role == QtCore.Qt.ItemDataRole.EditRole:
            return value
        return None

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        if len(self._data) > 0:
            return len(self._data[0])
        return 0

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return self._headers[section]
            elif orientation == QtCore.Qt.Orientation.Vertical:
                return str(section + 1)
        return None

    def flags(self, index):
        return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable

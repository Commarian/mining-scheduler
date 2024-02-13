from PyQt6 import QtCore, QtWidgets

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, headers=None):
        super(TableModel, self).__init__()
        self._data = data
        self._headers = headers if headers else ['Header 1', 'Header 2']

    def data(self, index, role):
        return self._data[index.row()][index.column()]

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        return len(self._data[0])

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Orientation.Horizontal:
                return self._headers[section]
            elif orientation == QtCore.Qt.Orientation.Vertical:
                return str(section + 1)
        return None

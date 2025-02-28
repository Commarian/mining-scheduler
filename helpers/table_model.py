from PyQt5 import QtCore, QtGui, QtWidgets

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data, headers):
        super(TableModel, self).__init__()
        self._data = data
        self._headers = headers

    def data(self, index, role):
        # Get the cell value normally
        value = self._data[index.row()][index.column()]

        # For normal display
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return value

        # Customize the font appearance
        if role == QtCore.Qt.ItemDataRole.FontRole:
            # Get the entire row
            row_data = self._data[index.row()]
            # Make sure there are enough columns (Overdue and Status are columns 10 and 11)
            if len(row_data) >= 12:
                overdue = row_data[10]
                status = row_data[11]
                font = QtGui.QFont()
                # If overdue and still open, underline the text
                if overdue == "Yes" and status == "Open":
                    font.setUnderline(True)
                return font

        # Customize the text color
        if role == QtCore.Qt.ItemDataRole.ForegroundRole:
            row_data = self._data[index.row()]
            if len(row_data) >= 12:
                overdue = row_data[10]
                status = row_data[11]
                # Red text for overdue open issues, grey for overdue but closed
                if overdue == "Yes":
                    if status == "Open":
                        return QtGui.QBrush(QtGui.QColor("red"))
                    else:
                        return QtGui.QBrush(QtGui.QColor("gray"))

        if role == QtCore.Qt.ItemDataRole.EditRole:
            return value

        return None

    def rowCount(self, parent):
        return len(self._data)

    def columnCount(self, parent):
        if self._data:
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
        return (QtCore.Qt.ItemFlag.ItemIsEnabled | 
                QtCore.Qt.ItemFlag.ItemIsSelectable)

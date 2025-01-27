from PyQt5 import QtWidgets, QtCore



class MyTableView(QtWidgets.QTableView):
    rowSelected = QtCore.pyqtSignal(list)
    def __init__(self, model):
        super(MyTableView, self).__init__()

        self.setModel(model)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.clicked.connect(self.handleRowSelection)


    def handleRowSelection(self, index):
        # Get the clicked index and select the entire row
        selection_model = self.selectionModel()
        selection_model.select(index.siblingAtColumn(0), QtCore.QItemSelectionModel.SelectionFlag.Select)
        selection_model.select(index.siblingAtColumn(1), QtCore.QItemSelectionModel.SelectionFlag.Select)

        # Perform the desired action here, e.g., print the selected row data
        selected_row = [self.model().data(index.siblingAtColumn(col), QtCore.Qt.ItemDataRole.DisplayRole) for col in
                        range(self.model().columnCount(QtCore.QModelIndex()))]


        print("Selected Row:", selected_row)
        self.rowSelected.emit(selected_row)


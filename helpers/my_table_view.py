from PyQt5 import QtWidgets, QtCore

import statics



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
        statics.row_selected = index.row()
        
    


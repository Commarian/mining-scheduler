from PyQt5.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionProgressBar, QApplication
from PyQt5.QtCore import Qt

class ProgressBarDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Get the progress value
        value = index.data()
        try:
            progress = int(value)
        except:
            progress = 0

        # Create the style option for the progress bar
        progressBarOption = QStyleOptionProgressBar()
        progressBarOption.rect = option.rect  # or apply a margin if you like
        progressBarOption.minimum = 0
        progressBarOption.maximum = 100
        progressBarOption.progress = progress
        progressBarOption.text = str(progress) + "%"  # remove f-string
        progressBarOption.textVisible = True

        # If the row is selected, show selection highlight
        if option.state & QStyle.State_Selected:
            progressBarOption.state = QStyle.State_Enabled | QStyle.State_Selected
        else:
            progressBarOption.state = QStyle.State_Enabled

        # Draw the progress bar
        painter.save()
        QApplication.style().drawControl(QStyle.CE_ProgressBar, progressBarOption, painter)
        painter.restore()

    def createEditor(self, parent, option, index):
        # We disable inline editing in the table itself
        return None

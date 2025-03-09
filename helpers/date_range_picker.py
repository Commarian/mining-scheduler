from PyQt5.QtWidgets import QCalendarWidget
from PyQt5.QtCore import QDate, Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QCalendarWidget
from PyQt5.QtCore import QDate, Qt, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import QSettings  # <-- Import QSettings
import statics
from helpers import custom_calendar

class DateRangePicker(custom_calendar.CustomCalendar):
    """
    This widget lets a user select a start date on the first click
    and an end date on the second click, using QCalendarWidget in SingleSelection mode.
    """
    dateRangeSelected = pyqtSignal(QDate, QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_date = None
        self.end_date = None

        # We use SingleSelection so that QCalendarWidget
        # actually lets us click and highlight individual days.
        self.setSelectionMode(QCalendarWidget.SingleSelection)

        # Connect selectionChanged, which fires whenever the user picks a day.

        # Decide which highlight color to use for our range
        self.dark_mode = QSettings("Springbok", "SpringbokApp").value("dark_mode", False, type=bool)
        if self.dark_mode:
            # e.g. a more gold-ish color in the dark
            self.highlight_color = QColor(255, 215, 0, 100)  
        else:
            # a softer yellow in light mode
            self.highlight_color = QColor(200, 200, 0, 100)

        # Connect selectionChanged, which fires whenever the user picks a day.
        self.selectionChanged.connect(self.handle_selection_changed)

    def handle_selection_changed(self):
        # This method fires every time a user picks a day in SingleSelection mode.
        selected_day = self.selectedDate()

        # If we have no start date or we already had a full range, reset
        if self.start_date is None or (self.start_date and self.end_date):
            self.start_date = selected_day
            self.end_date = None
        else:
            # We already have a start_date but not an end_date => set end_date
            if selected_day < self.start_date:
                # Swap if needed
                self.end_date = self.start_date
                self.start_date = selected_day
            else:
                self.end_date = selected_day

            # Emit the signal now that we have a full range
            self.dateRangeSelected.emit(self.start_date, self.end_date)

        # Force the widget to repaint with our highlight logic
        self.updateCells()

    def paintCell(self, painter, rect, date):
        # Let QCalendarWidget handle the basic cell look
        super().paintCell(painter, rect, date)
        # If we want a special highlight for today's date (even if not selected):
        if date == QDate.currentDate():
            painter.save()
            pen = QPen(QColor("green"), 2)  # thicker red pen
            painter.setPen(pen)
            # Draw the rectangle *inside* the cell rect
            painter.drawRect(rect.adjusted(1, 1, -1, -1))
            painter.restore()

        if self.start_date and not self.end_date:
            # Only start date selected => highlight that cell
            if date == self.start_date:
                painter.save()
                painter.fillRect(rect, self.highlight_color)
                painter.restore()
        elif self.start_date and self.end_date:
            # Full range => highlight everything in [start_date, end_date]
            if self.start_date <= date <= self.end_date:
                painter.save()
                painter.fillRect(rect, self.highlight_color)
                painter.restore()
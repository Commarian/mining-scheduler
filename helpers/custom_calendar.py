from PyQt5.QtWidgets import QCalendarWidget, QToolButton, QMenu, QSpinBox
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QBrush, QColor

class CustomCalendar(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 1. If you want to forbid selecting dates before "today", do:
        self.setMinimumDate(QDate.currentDate())

        # 2. Start the user on today's page:
        self.setSelectedDate(QDate.currentDate())

        #
        # Find the navigation subwidgets
        #

        # Month button that opens the month menu
        self.month_button = self.findChild(QToolButton, "qt_calendar_monthbutton")

        # The year spinbox (the textual box that shows the year)
        self.year_spin = self.findChild(QSpinBox, "qt_calendar_yearedit")

        if self.month_button:
            # The QToolButton has an associated QMenu
            # We can connect to the menu's "aboutToShow" signal
            self.month_menu = self.month_button.findChild(QMenu)
            if self.month_menu:
                self.month_menu.aboutToShow.connect(self.updateMonthMenu)

        if self.month_menu:
            self.month_menu.setStyleSheet("""
                QMenu::item:disabled {
                    color: #888888; 
                    background-color: #dcdcdc;
                }
            """)
            
        # If you want to do something when the year changes, connect a slot
        if self.year_spin:
            self.year_spin.valueChanged.connect(self.yearChanged)

        # ... any other setup ...
    
    def yearChanged(self, new_year):
        """
        Called when the user spins the year in the QSpinBox.
        We can forcibly close/reopen the month menu or do other logic
        that depends on the year.
        """
        self.updateMonthMenu(new_year)

    def updateMonthMenu(self, new_year = None):
        """
        Called right before the month menu is shown.
        Here, we can disable months older than the current date,
        and also highlight the current month in green if it's in the current year.
        """
        # If for some reason it's null, do nothing
        if not self.month_menu:
            return

        # Get today's date
        today = QDate.currentDate()
        current_year = today.year()
        current_month = today.month()  # 1..12

        # Figure out which year is currently selected in the calendar
        # Usually it's from the spin box we found above:
        if self.year_spin:
            selected_year = self.year_spin.value()
            if new_year:
                selected_year = new_year

        # The month menu typically has 12 actions for Jan..Dec in order
        actions = self.month_menu.actions()  # list of QActions
        for i, action in enumerate(actions):
                
            # i goes from 0..11 => "January".. "December"
            month_index = i + 1
            # 2) Decide if we want to disable or enable this month
            if selected_year < current_year:
                # If user is in a past year, maybe we want to allow all months
                action.setEnabled(False)

            elif selected_year > current_year:
                # If user is in a future year, allow all months
                action.setEnabled(True)
                action.setVisible(True)

            else:
                # selected_year == current_year
                # Disable months that come before today's month
                if month_index < current_month:
                    action.setEnabled(False)
                    action.setVisible(False)
                else:
                    action.setEnabled(True)
                    action.setVisible(True)


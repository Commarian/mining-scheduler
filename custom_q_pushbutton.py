from PyQt5.QtWidgets import QPushButton

green_button_style = """
    QPushButton { background-color: #4CAF50; color: white; border: 1px solid #4CAF50; }
        QPushButton:disabled {
            background-color: #CCCCCC;  /* Custom color for disabled state */
            color: #666666;  /* Custom text color for disabled state */
        }
    """
red_button_style = """
    QPushButton { background-color: #fc0328; color: white; border: 1px solid #4CAF50; }
        QPushButton:disabled {
            background-color: #CCCCCC;  /* Custom color for disabled state */
            color: #666666;  /* Custom text color for disabled state */
        }
    """
def generate_button(text):
    btn = QPushButton(text)
    btn.setMinimumSize(60, 28)
    btn.setMaximumSize(100, 33)
    if text.lower().__contains__("exit"):
        btn.setStyleSheet(red_button_style)
    else:
        btn.setStyleSheet(green_button_style)
    return btn

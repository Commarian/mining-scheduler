from PyQt5.QtWidgets import QDialog, QVBoxLayout, QProgressBar, QSlider, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt

class ProgressDialog(QDialog):
    def __init__(self, current_progress=0, parent=None):
        super(ProgressDialog, self).__init__(parent)
        self.setWindowTitle("Update Progress")
        self.current_progress = current_progress
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(self.current_progress)
        
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(0, 100)
        self.slider.setValue(self.current_progress)
        self.slider.valueChanged.connect(self.progress_bar.setValue)
        
        layout.addWidget(QLabel("Progress:"))
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.slider)
        
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save", self)
        self.cancel_btn = QPushButton("Cancel", self)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
    def get_progress(self):
        return self.slider.value()
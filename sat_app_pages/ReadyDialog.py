from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt

class ReadyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Ready to Begin?")
        self.setFixedSize(420, 250)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        title = QLabel("Ready to Begin?")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 22px; font-weight: bold;"
        )

        instructions = QLabel(
            "You will complete a series of SAT questions.\n\n"
            "You will have 90 seconds to answer each question.\n\n"
            "Click Begin when you are ready"
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)

        begin_btn = QPushButton("Begin")
        begin_btn.setMinimumHeight(45)
        begin_btn.clicked.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(instructions)
        layout.addWidget(begin_btn)
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt

class ReadyDialog(QDialog):
    def __init__(self, parent=None, training=False):
        super().__init__(parent)

        self.is_training = training

        self.setWindowTitle("Ready to Begin?")
        self.setFixedSize(420, 250)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        if self.is_training:
            title = QLabel("Training")

            instructions = QLabel(
                "You will complete a series of training questions.\n\n"
                "Answer these questions within the time limit provided.\n\n"
                "Click BEGIN when you are ready"
            )
        
        else:
            title = QLabel("Ready to Begin Experiment")

            instructions = QLabel(
                "You will complete a series of SAT questions.\n\n"
                "You will have 90 seconds to answer each question.\n\n"
                "Let your study administrator know you are ready to begin."
            )

        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 22px; font-weight: bold;"
        )

        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)

        begin_btn = QPushButton("BEGIN")
        begin_btn.setMinimumHeight(45)
        begin_btn.clicked.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(instructions)
        layout.addWidget(begin_btn)
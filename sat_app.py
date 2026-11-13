"""
SAT Practice + YouTube player

Install:   pip install PyQt6 PyQt6-WebEngine
Run:       python sat_app.py
"""

import sys
import re

from sat_app_pages.SatWindow import SatWindow
from sat_app_pages.ReadyDialog import ReadyDialog

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import (
    QApplication, QDialog
)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    pal = QPalette()  # force a light theme so system dark mode can't wash out the text
    for role, color in [
        (QPalette.ColorRole.Window, "#f5f6fa"), (QPalette.ColorRole.WindowText, "#000000"),
        (QPalette.ColorRole.Base, "#ffffff"), (QPalette.ColorRole.AlternateBase, "#f0f0f0"),
        (QPalette.ColorRole.Text, "#000000"), (QPalette.ColorRole.Button, "#ffffff"),
        (QPalette.ColorRole.ButtonText, "#000000"), (QPalette.ColorRole.ToolTipBase, "#ffffff"),
        (QPalette.ColorRole.ToolTipText, "#000000"), (QPalette.ColorRole.PlaceholderText, "#555555"),
    ]:
        pal.setColor(role, QColor(color))
    app.setPalette(pal)

    win = SatWindow()
    win.show()

    dialog = ReadyDialog(win, training=True)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        win.start_training()
        #win.start_experiment()
    else:
        win.close()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

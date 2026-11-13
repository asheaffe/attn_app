import csv
import json
import os
import random
import re
import sys
import time
import requests
import html
import re

from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QActionGroup, QColor, QGuiApplication, QKeySequence, QPalette, QShortcut
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication, QButtonGroup, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QRadioButton,
    QSplitter, QVBoxLayout, QWidget, QSizePolicy, QScrollArea
)


# sometimes the json files provided by API will have things like \\pi which isn't recognized as latex
LATEX_PATTERN = re.compile(
    r"\\(?:frac|dfrac|tfrac|sqrt|pi|theta|alpha|beta|"
    r"times|div|cdot|leq|geq|neq|pm|infty|"
    r"sin|cos|tan|sum|int|left|right)\b"
)

def prepare_latex(text):
    text = str(text or "").strip()

    # if already formatted with proper delimiters (latex or mathjax)
    if (
        r"\(" in text
        or r"\[" in text
        or "$" in text
    ):
        return text
    
    # no delimiter, add them in
    if LATEX_PATTERN.search(text):
        return r"\(" + text + r"\)"
    
    return text

class LatexWidget(QWebEngineView):
    def __init__(self, parent=None, objectName=None):
        super().__init__(parent)

        if objectName is not None:
            self.setObjectName(objectName)

        self._alignment = Qt.AlignmentFlag.AlignLeft
        self._word_wrap = True
        self._text = ""

        self.setMinimumHeight(100)

        # Avoid nested scrollbars
        self.page().setBackgroundColor(Qt.GlobalColor.transparent)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        self.setMinimumHeight(30)

        self.loadFinished.connect(self._update_height)
    
    def _update_height(self, ok=True):
        if not ok:
            return

        # Wait for MathJax, then measure the document height
        self.page().runJavaScript("""
            if (window.MathJax && MathJax.startup) {
                MathJax.startup.promise.then(() => {
                    document.body.dataset.mathReady = "true";
                });
            } else {
                document.body.dataset.mathReady = "true";
            }
        """)

        self._measure_height()


    def _measure_height(self):
        self.page().runJavaScript("""
            Math.ceil(Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight
            ))
        """, self._apply_height)


    def _apply_height(self, height):
        if not isinstance(height, (int, float)):
            return

        new_height = max(30, int(height) + 4)

        if self.height() != new_height:
            self.setFixedHeight(new_height)



    def setWordWrap(self, enabled):
        """
        Compatibility method for QLabel.setWordWrap().
        """
        self._word_wrap = enabled
        self._render()

    def setAlignment(self, alignment):
        """
        Compatibility method for QLabel.setAlignment().
        """
        self._alignment = alignment
        self._render()

    def setText(self, text):
        """
        Compatibility method for QLabel.setText().
        """
        self._text = prepare_latex(text)
        self._render()

    def text(self):
        return self._text

    def _render(self):
        if self._alignment & Qt.AlignmentFlag.AlignHCenter:
            alignment = "center"
        elif self._alignment & Qt.AlignmentFlag.AlignRight:
            alignment = "right"
        else:
            alignment = "left"

        safe_text = html.escape(self._text)
        safe_text = safe_text.replace("\n", "<br>")

        wrap_style = (
            "overflow-wrap: break-word;"
            if self._word_wrap
            else "white-space: nowrap;"
        )

        page = r"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">

            <script>
                window.MathJax = {
                    tex: {
                        inlineMath: [['$', '$'], ['\\(', '\\)']],
                        displayMath: [['$$', '$$'], ['\\[', '\\]']]
                    }
                };
            </script>

            <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>

            <style>
                body {
                    font-family: Arial, sans-serif;
                    font-size: 18px;
                    line-height: 1.6;
                    margin: 8px;
                    color: #222;
                }

                mjx-container {
                    max-width: 100%;
                }
            </style>
        </head>

        <body style="text-align: __ALIGN__; __WRAP__">
            __CONTENT__
        </body>
        </html>
        """

        page = (
            page.replace("__ALIGN__", alignment)
                .replace("__WRAP__", wrap_style)
                .replace("__CONTENT__", safe_text)
        )

        self.setHtml(page, QUrl("https://cdn.jsdelivr.net/"))
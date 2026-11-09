"""
SAT Practice + YouTube player

Install:   pip install PyQt6 PyQt6-WebEngine
Run:       python sat_app.py

- Main window: SAT-style multiple-choice practice at three difficulty levels:
  Reading Comprehension, Vocabulary in Context, and Math (No Calculator), where
  every math question can be solved by hand.
- The YouTube player sits to the right of the questions, side by side (drag the divider to resize).
  Paste any YouTube link (video, youtu.be, shorts, or playlist) and press Play.
- The video follows the difficulty of the question on screen:
    Easy          -> video plays normally
    Intermediate  -> picture hidden, audio keeps playing at a lower volume
    Hard          -> video paused completely
- Sessions contain an equal number of easy, intermediate and hard questions (Session menu: can be turned off).
- Optional (Session menu, off by default): hold hard questions until the second half of a session.
- Every answer is saved to a CSV (sat_results.csv next to this script): how long you took, and
  whether you were right. File > Choose results CSV file... changes where it goes.
- Video setting, using the buttons above the player (also in the Video menu):
    By difficulty ........ the behaviour described above (default)
    Always on / off ...... the video is on (or off) for every question
    Test: half on, half off ... an on-vs-off test within one session. Which half has the video on is
                                chosen at random each session (every restart), so sometimes it's on first
                                and sometimes off first. The order is recorded in the CSV.
- File > Load questions (JSON)... lets you add your own questions.
  Format: a list of objects like
    {"section": "Reading Comprehension", "level": "easy", "passage": "(optional)", "prompt": "...",
     "choices": ["a", "b", "c", "d"], "answer": 0, "explanation": "..."}
  where "answer" is the 0-based index of the correct choice, and "level" is
  "easy", "intermediate" or "hard" (optional, defaults to "intermediate").
"""

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

BASE_DIR = Path(__file__).resolve().parent
BASE_URL = "https://pinesat.duckdns.org/api/questions"

DIFFICULTY_MAP = {
    "easy": "easy",
    "medium": "intermediate",
    "intermediate": "intermediate",
    "hard": "hard"
}

ANSWER_MAP = {"A": 0, "B": 1, "C": 2, "D": 3}

LETTERS = "ABCD"

def make_question_req(section="english", limit=10, domain=None):
    params = {
        "section": section,
        "limit": limit
    }

    if domain:
        params["domain"] = domain

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()

def load_questions(file_path):
    file_path = Path(file_path)

    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected a JSON list of questions.")
    
    questions = []

    for item in data:
        try:
            q = item["question"]

            difficulty = DIFFICULTY_MAP[
                item["difficulty"].strip().lower()
            ]

            choices = [
                q["choices"][letter]
                for letter in ("A", "B", "C", "D")
            ]

            answer = ANSWER_MAP[
                q["correct_answer"].strip().upper()
            ]

            passage = (q.get("paragraph") or "").strip()
            question_text = (q.get("question") or "").strip()

            prompt = question_text

            if not prompt:
                raise ValueError("Missing question text")
            
            visuals = item.get("visuals") or {}

            questions.append({
                "id": item.get("id"),
                "section": item.get("domain", "Reading"),
                "level": difficulty,
                "passage": passage,
                "prompt": prompt,
                "choices": choices,
                "answer": answer,
                "explanation": q.get("explanation", ""),
                "visuals": visuals,
            })

        except (KeyError, ValueError, TypeError) as exc:
            print(
                f"Skipping question "
                f"{item.get('id', 'unknown')}: {exc}"
            )

    return questions

QUESTIONS = load_questions(BASE_DIR / "data-files" / "opensat_questions.json")

CSV_FIELDS = ["timestamp", "session_id", "question_number", "session_half", "section", "level", "question",
              "chosen_answer", "correct_answer", "correct", "seconds_to_answer",
              "video_setting", "condition_order", "video_on", "video_loaded", "video_mode"]
VIDEO_SETTINGS = {"follow": "follow_difficulty", "on": "always_on", "off": "always_off",
                  "half": "half_on_half_off_random_order"}

# Question difficulty -> what the video does
VIDEO_MODE = {"easy": "video", "intermediate": "audio", "hard": "pause"}
VOLUME = {"video": 100, "audio": 30, "pause": 100, "off": 100}   # % volume per mode (audio = intermediate questions)
SPEED = {"video": 1, "audio": 1, "pause": 1, "off": 1}          # playback speed per mode (YouTube allows 0.25-2)
MODE_LABEL = {"video": "▶ Video on", "audio": f"🎧 Audio only · {VOLUME['audio']}% volume",
              "pause": "⏸ Paused", "off": "⏹ Video off"}

# --------------------------------------------------------------------------
# YouTube helpers
# --------------------------------------------------------------------------
def youtube_embed_url(text: str):
    """Turn a pasted YouTube link / ID into an embeddable URL (or None)."""
    text = text.strip()
    if not text:
        return None
    m_list = re.search(r"[?&]list=([\w-]+)", text)
    m_vid = re.search(r"(?:v=|youtu\.be/|/embed/|/shorts/|/live/)([\w-]{11})", text)
    if m_vid:
        url = f"https://www.youtube.com/embed/{m_vid.group(1)}?autoplay=1&rel=0"
        if m_list:
            url += f"&list={m_list.group(1)}"
        return url
    if m_list:
        return f"https://www.youtube.com/embed/videoseries?list={m_list.group(1)}&autoplay=1"
    if re.fullmatch(r"[\w-]{11}", text):
        return f"https://www.youtube.com/embed/{text}?autoplay=1&rel=0"
    return None


PLAYER_HTML = """<html><body style="margin:0;background:#000">
<iframe id="yt" src="__SRC__" style="position:absolute;inset:0;width:100%;height:100%;border:0"
  allow="autoplay; encrypted-media; picture-in-picture"
  referrerpolicy="strict-origin-when-cross-origin"></iframe>
<div id="cover" style="position:absolute;inset:0;display:none;align-items:center;justify-content:center;
  background:#e9ecf5;color:#000;font:600 16px sans-serif;text-align:center;padding:16px"></div>
<script>
var VOL=__VOL__, RATE=__RATE__, cur="__MODE__";
function cmd(f,a){document.getElementById("yt").contentWindow.postMessage(
  JSON.stringify({event:"command",func:f,args:a===undefined?"":a}),"*");}
function vol(m){cmd("setVolume",[VOL[m]]);}
function rate(m){cmd("setPlaybackRate",[RATE[m]]);}
function tune(m){cmd("unMute");vol(m);rate(m);}
function cover(m){var c=document.getElementById("cover");
  if(m==="audio"){c.textContent="\uD83C\uDFA7 Audio only";c.style.display="flex";}
  else if(m==="pause"){c.textContent="\u23F8 Paused during hard questions";c.style.display="flex";}
  else if(m==="off"){c.textContent="\u23F9 Video is off";c.style.display="flex";}
  else{c.style.display="none";}}
function setMode(m){cur=m;cover(m);tune(m);cmd(m==="pause"||m==="off"?"pauseVideo":"playVideo");}
cover(cur);
// The YouTube player needs a moment to start listening, so apply volume/speed a few times after load.
function applySettingsSoon(){[500,1500,3000,6000].forEach(function(t){setTimeout(function(){tune(cur);},t);});}
document.getElementById("yt").addEventListener("load",applySettingsSoon);
applySettingsSoon();
</script></body></html>"""

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


class VideoPanel(QWidget):
    """YouTube player shown beside the questions, with on-screen always-on / always-off buttons."""

    setting_changed = pyqtSignal(str)   # "follow" | "on" | "off"

    def __init__(self):
        super().__init__()
        self.setObjectName("videoPanel")
        self.setMinimumWidth(380)
        self.mode = "video"   # "video" | "audio" | "pause" | "off"
        self.has_video = False   # True once a YouTube link has been loaded with Play
        self.status = QLabel(MODE_LABEL[self.mode])

        # self.url_input = QLineEdit()
        # self.url_input.setPlaceholderText("Paste a YouTube link…")
        #self.url_input.returnPressed.connect(self.play)
        play_btn = QPushButton("Play")
        play_btn.clicked.connect(self.play)
        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(self.stop)

        bar = QHBoxLayout()
        #bar.addWidget(self.url_input, 1)
        bar.addWidget(play_btn)
        bar.addWidget(stop_btn)

        # Segmented control: should the video follow the question difficulty, or always be on / off?
        self.setting_group = QButtonGroup(self)
        self.setting_group.setExclusive(True)
        self.setting_buttons = {}
        seg = QGridLayout()
        seg.addWidget(QLabel("Video:"), 0, 0)
        placement = {"follow": (0, 1, 1, 1), "on": (0, 2, 1, 1), "off": (0, 3, 1, 1), "half": (1, 1, 1, 3)}
        # for key, label in (("follow", "By difficulty"), ("on", "Always on"), ("off", "Always off"),
        #                    ("half", "Test: half on, half off (random order)")):
        #     b = QPushButton(label, objectName="seg")
        #     b.setCheckable(True)
        #     b.setChecked(key == "follow")
        #     b.clicked.connect(lambda _checked, k=key: self.setting_changed.emit(k))
        #     self.setting_group.addButton(b)
        #     self.setting_buttons[key] = b
        #     seg.addWidget(b, *placement[key])
        # seg.setColumnStretch(4, 1)

        self.view = QWebEngineView()
        self.view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        self.view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        self.view.page().fullScreenRequested.connect(lambda req: req.reject())
        self.stop()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        header = QHBoxLayout()
        header.addWidget(QLabel("YouTube player"))
        header.addStretch(1)
        header.addWidget(self.status)
        layout.addLayout(header)
        layout.addLayout(seg)
        layout.addLayout(bar)
        layout.addWidget(self.view, 1)

    def show_setting(self, key):
        """Reflect the current setting on the buttons (without emitting a change)."""
        self.setting_buttons[key].setChecked(True)

    def play(self):
        src = youtube_embed_url("https://www.youtube.com/watch?v=1baVt4UrP3k")
        if not src:
            self.show_message("That doesn't look like a YouTube link.")
            return
        # Start in whatever state the current question calls for.
        autoplay = 0 if self.mode in ("pause", "off") else 1
        src = src.replace("autoplay=1", f"autoplay={autoplay}")
        src += "&enablejsapi=1&origin=https%3A%2F%2Flocalhost"
        html = PLAYER_HTML.replace("__SRC__", src).replace("__MODE__", self.mode).replace("__VOL__", json.dumps(VOLUME)).replace("__RATE__", json.dumps(SPEED))
        # A real-looking base URL gives YouTube the origin/referrer it wants for embeds.
        self.view.setHtml(html, QUrl("https://localhost/"))
        self.has_video = True

    def set_mode(self, mode):
        """Switch between video / audio-only / paused / off (only acts on a change)."""
        if mode == self.mode:
            return
        self.mode = mode
        self.status.setText(MODE_LABEL[mode])
        self.view.page().runJavaScript(f'if (typeof setMode === "function") setMode("{mode}");')

    def stop(self):
        self.has_video = False
        self.show_message("Paste a YouTube link above and press Play.")

    def show_message(self, msg):
        self.view.setHtml(
            '<body style="margin:0;background:#111;color:#aaa;font:14px sans-serif;'
            f'display:flex;align-items:center;justify-content:center;height:100vh">{msg}</body>')


# --------------------------------------------------------------------------
# Main SAT window
# --------------------------------------------------------------------------
STYLE = """
QWidget { color: #000000; }
QMainWindow, QWidget#root { background: #f5f6fa; }
QWidget#videoPanel { background: #fff; border: 1px solid #c4c8d6; border-radius: 8px; }
QLabel#passage { background: #fff; border: 1px solid #d9dce6; border-radius: 8px; padding: 14px; font-size: 15px; }
QLabel#prompt { font-size: 18px; }
QLabel#meta { color: #000; font-size: 13px; }
QRadioButton { background: #fff; border: 1px solid #d9dce6; border-radius: 8px; padding: 12px; font-size: 16px; }
QRadioButton:hover:enabled { border-color: #4a6cf7; }
QRadioButton:checked { border: 2px solid #4a6cf7; }
QPushButton { padding: 8px 18px; border-radius: 6px; border: 1px solid #c4c8d6; background: #fff; font-size: 14px; }
QPushButton:hover { background: #eef1ff; }
QPushButton#primary { background: #cfd8ff; color: #000; border: none; font-weight: bold; }
QPushButton#primary:hover { background: #b6c4ff; }
QPushButton:disabled { color: #777; }
QPushButton#seg { padding: 6px 6px; font-size: 13px; }
QPushButton:checked { background: #b6c4ff; border: 1px solid #4a6cf7; }
html, body {
    margin: 0;
    padding: 0;
    overflow: hidden;
}

body {
    font-family: Arial, sans-serif;
    font-size: 18px;
    line-height: 1.6;
    overflow-wrap: break-word;
}
"""


class SatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.video = VideoPanel()
        self.video.setting_changed.connect(self.set_video_setting)
        self.video_actions = {}
        self.all_questions = list(QUESTIONS)
        self.pool, self.results, self.i = [], {}, 0
        self.video_setting = "half"          # "follow" | "on" | "off" | "half"
        self.hold_hard_late = False            # hard questions only in the 2nd half (off by default)
        self.balance_levels = True             # equal number of easy / intermediate / hard per session
        self._checked_path = None
        self.half_order = random.choice(["on_first", "off_first"])           # "on_first" | "off_first" (re-randomized every session)
        self.results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"data-files/sat_results.csv")
        self.session_id = ""
        self.q_elapsed, self.q_shown_at = {}, None   # per-question time on screen (seconds)
        self._warned_csv = False

        self.elapsed_seconds = 0
        self.answer_submitted = False

        self.timer = QTimer(self)
        self.timer.setInterval(1000)    # updates every second
        self.timer.timeout.connect(self.update_timer)

        self.setWindowTitle("SAT Practice")
        geo = QGuiApplication.primaryScreen().availableGeometry()
        self.resize(min(geo.width(), 1500), min(geo.height(), 860))
        self.setStyleSheet(STYLE)
        self._build_ui()
        self._build_menu()
        self.start_session()

    # ---- UI ----
    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        v = QVBoxLayout(root)
        v.setContentsMargins(28, 20, 28, 20)
        v.setSpacing(12)

        top = QHBoxLayout()
        self.section_box = QComboBox()
        self.section_box.currentIndexChanged.connect(self.start_session)
        self.level_box = QComboBox()
        self.level_box.addItems(["All", "Easy", "Intermediate", "Hard"])
        self.level_box.currentIndexChanged.connect(self.start_session)
        self.meta = QLabel(objectName="meta")
        self.video_btn = QPushButton("Show / hide video")
        self.video_btn.clicked.connect(self.toggle_video)
        self.timer_label = QLabel("Time: 00:00")

        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.timer_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #ffffff;
                background-color: #303030;
                padding: 10px;
                border-radius: 6px;
            }        
        """)

        # timer starts on button press
        self.start_timer_button = QPushButton("Start Timer")
        self.start_timer_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
            }

            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.start_timer_button.clicked.connect(self.timer.start)

        top.addWidget(QLabel("Section:"))
        top.addWidget(self.section_box)
        top.addWidget(QLabel("Difficulty:"))
        top.addWidget(self.level_box)
        top.addStretch(1)
        #top.addWidget(self.video_btn)
        top.addWidget(self.start_timer_button)
        top.addWidget(self.timer_label)
        v.addLayout(top)
        v.addWidget(self.meta)

        question_scroll = QScrollArea()
        question_scroll.setWidgetResizable(True)
        question_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        question_content = QWidget()
        question_layout = QVBoxLayout(question_content)

        question_layout.setSpacing(12)
        question_layout.setContentsMargins(5, 5, 5, 5)

        question_scroll = QScrollArea()
        question_scroll.setWidgetResizable(True)

        question_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        question_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        question_scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        question_content = QWidget()
        question_layout = QVBoxLayout(question_content)

        question_layout.setContentsMargins(5, 5, 5, 5)
        question_layout.setSpacing(12)

        self.passage = LatexWidget(objectName="passage")
        self.passage.setMinimumWidth(0)
        self.passage.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred
        )

        self.prompt = LatexWidget(objectName="prompt")
        self.prompt.setMinimumWidth(0)
        self.prompt.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred
        )
        # self.calc_tag = QLabel("No calculator needed: every question in this section can be done by hand.")
        # self.calc_tag.setStyleSheet("font-size: 13px; font-weight: bold;")
        #v.addWidget(self.calc_tag)
        question_layout.addWidget(self.passage)
        question_layout.addWidget(self.prompt)

        self.group = QButtonGroup(self)
        self.radios = []
        self.choice_labels = []

        for k in range(4):
            r = QRadioButton()
            label = LatexWidget()

            #label.setWordWrap(True)
            label.setSizePolicy(
                QSizePolicy.Policy.Ignored,
                QSizePolicy.Policy.Preferred
            )

            r.setText(LETTERS[k])
            r.setSizePolicy(
                QSizePolicy.Policy.Fixed,
                QSizePolicy.Policy.Fixed,
            )

            row = QHBoxLayout()
            row.setSpacing(10)
            row.addWidget(r)
            row.addWidget(label, 1)

            label.mousePressEvent = lambda event, radio=r: (
                radio.setChecked(True) if radio.isEnabled() else None
            )

            self.group.addButton(r, k)
            self.radios.append(r)
            self.choice_labels.append(label)

            question_layout.addLayout(row)

        self.feedback = QLabel()
        #self.feedback.setWordWrap(True)
        self.feedback.setStyleSheet("font-size: 15px; color: #000;")
        question_layout.addWidget(self.feedback)
        question_layout.addStretch(1)

        question_scroll.setWidget(question_content)
        v.addWidget(question_scroll, 1)

        btns = QHBoxLayout()
        self.prev_btn = QPushButton("← Previous")
        #self.submit_btn = QPushButton("Submit", objectName="primary")

        self.next_btn = QPushButton("Submit", objectName="primary")
        #self.restart_btn = QPushButton("Restart / reshuffle")
        self.prev_btn.clicked.connect(lambda: self.go(-1))
        # self.next_btn.clicked.connect(lambda: self.go(+1))
        self.next_btn.clicked.connect(self.handle_submit_next)
        #self.restart_btn.clicked.connect(self.start_session)
        for b in (self.prev_btn, self.next_btn):
            btns.addWidget(b)
        btns.addStretch(1)
        v.addLayout(btns)

        # allows the question panel to shrink independently of its content
        root.setMinimumWidth(0)
        root.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Expanding
        )

        # allow the video panel to occupy the right side of the screen
        self.video.setMinimumWidth(0)
        self.video.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        # side-by-side
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.splitter.addWidget(root)
        self.splitter.addWidget(self.video)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

        # start at approx 50/50 split
        self.splitter.setSizes([700, 700])

        self.splitter.setChildrenCollapsible(False)

        # Give both panels min usable width
        root.setMinimumWidth(300)
        self.video.setMinimumWidth(300)

        self.setCentralWidget(self.splitter)

        # Keyboard shortcuts: A-D choose, Enter submits, arrows navigate
        for k, key in enumerate("ABCD"):
            QShortcut(QKeySequence(key), self, activated=lambda k=k: self._pick(k))
        QShortcut(QKeySequence(Qt.Key.Key_Return), self, activated=self.submit)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, activated=lambda: self.go(+1))
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, activated=lambda: self.go(-1))

    def handle_submit_next(self):
        answered = self.i in self.results

        if answered:
            if self.i < len(self.pool) - 1:
                
                # answer has been submitted, move to next question
                self.go(+1)
        else:
            # submit current answer
            self.submit()

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("&File")
        load = QAction("Load questions (JSON)…", self)
        load.triggered.connect(self.load_json)
        file_menu.addAction(load)
        choose = QAction("Choose results CSV file…", self)
        choose.triggered.connect(self.choose_results_file)
        file_menu.addAction(choose)

        # video_menu = self.menuBar().addMenu("&Video")
        # group = QActionGroup(self)
        # group.setExclusive(True)
        # for key, label in (("follow", "Follow question difficulty"), ("on", "Always on"), ("off", "Always off"),
        #                    ("half", "Test: half on, half off (random order)")):
        #     act = QAction(label, self)
        #     act.setCheckable(True)
        #     act.setChecked(key == self.video_setting)
        #     act.triggered.connect(lambda _checked, k=key: self.set_video_setting(k))
        #     self.video_actions[key] = act
        #     group.addAction(act)
        #     video_menu.addAction(act)

        session_menu = self.menuBar().addMenu("&Session")
        balance = QAction("Equal number of easy, intermediate and hard questions", self)
        balance.setCheckable(True)
        balance.setChecked(self.balance_levels)
        balance.triggered.connect(self.set_balance)
        session_menu.addAction(balance)
        hold = QAction("Hold hard questions until the second half", self)
        hold.setCheckable(True)
        hold.setChecked(self.hold_hard_late)
        hold.triggered.connect(self.set_hold_hard)
        session_menu.addAction(hold)

        self.statusBar().showMessage(f"Saving results to: {self.results_path}")

    # ---- Session logic ----
    def refresh_sections(self):
        current = self.section_box.currentText()
        sections = ["All"] + sorted({q["section"] for q in self.all_questions})
        self.section_box.blockSignals(True)
        self.section_box.clear()
        self.section_box.addItems(sections)
        if current in sections:
            self.section_box.setCurrentText(current)
        self.section_box.blockSignals(False)

    def start_session(self):
        if self.section_box.count() == 0:
            self.refresh_sections()
        sec = self.section_box.currentText()
        lvl = self.level_box.currentText().lower()
        qs = [dict(q) for q in self.all_questions
              if sec in ("All", q["section"]) and lvl in ("all", q.get("level", "intermediate"))]
        
        if self.balance_levels and lvl == "all":
            # Equal numbers per level: draw as many from each level as the smallest level has.
            by_level = {
                level: [q for q in qs if q.get("level", "intermediate") == level]
                for level in ("easy", "intermediate", "hard")
            }

            # 60 questions total
            ### this is hard-coded, will want to set to change on input later ###
            target_counts = {
                "easy": 10,
                "intermediate": 10,
                "hard": 10
            }

            selected = []
            remaining = []

            for level, questions in by_level.items():
                random.shuffle(questions)

                count = min(target_counts[level], len(questions))

                selected.extend(questions[:count])
                remaining.extend(questions[count:])

            slots_left = 30 - len(selected)

            if slots_left > 0:
                selected.extend(
                    random.sample(
                        remaining,
                        min(slots_left, len(remaining))
                    )
                )
            qs = selected

        else:
            qs = random.sample(qs, min(30, len(qs)))

        random.shuffle(qs)

        self.elapsed_seconds = 0
        self.timer_label.setText("Time: 00:00")

        if self.hold_hard_late:   # optional: hard questions are held back until the second half
            not_hard = [q for q in qs if q.get("level", "intermediate") != "hard"]
            hard = [q for q in qs if q.get("level", "intermediate") == "hard"]
            half = len(qs) // 2
            if len(not_hard) >= half:
                first, rest = not_hard[:half], not_hard[half:] + hard
                random.shuffle(rest)
            else:  # not enough easier questions to fill the first half: use them all, then the hard ones
                first, rest = not_hard, hard
            qs = first + rest


        for q in qs:  # shuffle answer order, remembering the mapping
            q["order"] = random.sample(range(len(q["choices"])), len(q["choices"]))
        self.pool, self.results, self.i = qs, {}, 0
        self.q_elapsed, self.q_shown_at = {}, None
        self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{random.randrange(16 ** 3):03x}"
        self.half_order = random.choice(("on_first", "off_first"))   # randomize the on/off test order
        if self.video_setting == "half":
            self.statusBar().showMessage(self._half_message())
        self.show_question()

    def show_question(self):
        if not self.pool:
            self.prompt.setText("No questions in this section.")
            return
        q = self.pool[self.i]
        self.apply_video_mode()
        
        # self.passage.setVisible(bool(q.get("passage")))
        # self.passage.setText(q.get("passage", ""))

        passage = q.get("passage")
        if passage is None or str(passage).strip().lower() in ("null", ""):
            self.passage.hide()
        else:
            self.passage.setText(passage)
            self.passage.show()

        self.prompt.setText(q["prompt"])
    

        self.passage.setWordWrap(True)
        self.prompt.setWordWrap(True)
        
        self.passage.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        self.prompt.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        self.passage.setMinimumWidth(0)
        self.prompt.setMinimumWidth(0)

        self.group.setExclusive(False)
        for k, r in enumerate(self.radios):
            r.setChecked(False)

            label = self.choice_labels[k]

            if k < len(q["order"]):
                choice_text = q["choices"][q["order"][k]]

                label.setText(choice_text)

                r.setVisible(True)
                label.setVisible(True)

            else:
                r.setVisible(False)
                label.setVisible(False)

        self.group.setExclusive(True)

        self.feedback.clear()

        answered = self.i in self.results

        for r in self.radios:
            r.setEnabled(not answered)

        if answered:
            chosen = self.results[self.i]

            # restore previously selected answer
            self.radios[chosen].setChecked(True)

            # displays feedback
            self.show_feedback(q, chosen)

            # button advances to the next question
            self.next_btn.setText("Next")

        else:
            # question hasn't been answered
            self.next_btn.setText("Submit")

        self.prev_btn.setEnabled(self.i > 0)

        # disable next only if we're on the last question and it hasn't been answered
        self.next_btn.setEnabled(not answered or self.i < len(self.pool) - 1)

        self.update_meta() 

        if not answered:
            self._start_timer()

    def _pick(self, k):
        if self.i not in self.results and k < len(self.radios) and self.radios[k].isVisible():
            self.radios[k].setChecked(True)

    def submit(self):
        if not self.pool or self.i in self.results:
            return
        
        chosen = self.group.checkedId()
        if chosen < 0:
            self.feedback.setText("<b>Pick an answer first.</b>")
            return
        
        self.next_btn
        self._stop_timer()
        self.results[self.i] = chosen

        for r in self.radios:
            r.setEnabled(False)

        #self.next_btn.setEnabled(False)
        self.show_feedback(self.pool[self.i], chosen)

        self.update_meta()
        self.log_answer(self.pool[self.i], chosen)

    def show_feedback(self, q, chosen):
        correct_pos = q["order"].index(q["answer"])
        if chosen == correct_pos:
            head = "<b>✓ Correct!</b>"
        else:
            head = (f"<b>✗ Incorrect.</b> "
                    f"The correct answer is <b>{LETTERS[correct_pos]}</b>.")
        self.feedback.setText(f"{head}<br>{q.get('explanation', '')}")
    
        self.next_btn.setText("Next")

    def go(self, step):
        if self.pool and 0 <= self.i + step < len(self.pool):
            self._stop_timer()
            self.i += step
            self.show_question()

    def update_meta(self):
        right = sum(1 for i, c in self.results.items()
                    if c == self.pool[i]["order"].index(self.pool[i]["answer"]))
        level = self.pool[self.i].get("level", "intermediate").title()
        self.meta.setText(f"Question {self.i + 1} of {len(self.pool)}   |   Level: {level}   |   "
                          f"Score: {right}/{len(self.results)}")

    # ---- Timing + CSV results ----
    def _start_timer(self):
        """Start timing the question on screen (answered questions aren't timed again)."""
        self.q_shown_at = None if self.i in self.results else time.monotonic()

    def _stop_timer(self):
        """Add the time since the question appeared; time spent on other questions isn't counted."""
        if self.q_shown_at is not None:
            self.q_elapsed[self.i] = self.q_elapsed.get(self.i, 0.0) + (time.monotonic() - self.q_shown_at)
            self.q_shown_at = None

    def update_timer(self):
        self.elapsed_seconds += 1

        minutes = self.elapsed_seconds // 60
        seconds = self.elapsed_seconds % 60

        self.timer_label.setText(
            f"Time: {minutes:02d}:{seconds:02d}"
        )

    def log_answer(self, q, chosen):
        correct_pos = q["order"].index(q["answer"])
        row = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "session_id": self.session_id,
            "question_number": self.i + 1,
            "session_half": "first" if self._in_first_half(self.i) else "second",
            "section": q["section"],
            "level": q.get("level", "intermediate"),
            "question": " ".join(q["prompt"].split())[:120],
            "chosen_answer": q["choices"][q["order"][chosen]],
            "correct_answer": q["choices"][q["answer"]],
            "correct": int(chosen == correct_pos),
            "seconds_to_answer": round(self.q_elapsed.get(self.i, 0.0), 2),
            "video_setting": VIDEO_SETTINGS[self.video_setting],
            "condition_order": ({"on_first": "on_then_off", "off_first": "off_then_on"}[self.half_order]
                                if self.video_setting == "half" else ""),
            "video_on": int(self.video.mode == "video"),      # 1 = picture playing, 0 = off / paused / audio only
            "video_loaded": int(self.video.has_video),        # 0 = no YouTube link had been loaded yet
            "video_mode": self.video.mode,                    # video | audio (audio only) | pause | off
        }
        try:
            self._prepare_results_file()
            new_file = not os.path.exists(self.results_path) or os.path.getsize(self.results_path) == 0
            with open(self.results_path, "w" if new_file else "a", newline="",
                      encoding="utf-8-sig" if new_file else "utf-8") as f:   # BOM so Excel reads symbols right
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                if new_file:
                    writer.writeheader()
                writer.writerow(row)
            self.statusBar().showMessage(f"Saved to {self.results_path}")
        except OSError as e:
            self.statusBar().showMessage(f"Couldn't save results: {e}")
            if not self._warned_csv:
                self._warned_csv = True
                QMessageBox.warning(self, "Couldn't save results",
                                    f"{e}\n\nIf the CSV is open in Excel, close it. "
                                    "You can also pick a different file under File > Choose results CSV file…")

    def _prepare_results_file(self):
        """If an existing results file has different columns, move it aside so rows stay aligned."""
        if self._checked_path == self.results_path:
            return
        self._checked_path = self.results_path
        if os.path.exists(self.results_path) and os.path.getsize(self.results_path) > 0:
            with open(self.results_path, newline="", encoding="utf-8-sig") as f:
                header = next(csv.reader(f), [])
            if header != CSV_FIELDS:
                base, ext = os.path.splitext(self.results_path)
                backup = f"{base}_old_{datetime.now().strftime('%Y%m%d-%H%M%S')}{ext}"
                os.replace(self.results_path, backup)
                self.statusBar().showMessage(f"Older results file (different columns) kept as {backup}")

    def choose_results_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Choose results CSV file", self.results_path,
                                              "CSV files (*.csv)",
                                              options=QFileDialog.Option.DontConfirmOverwrite)
        if path:
            if not path.lower().endswith(".csv"):
                path += ".csv"
            self.results_path = path
            self._warned_csv = False
            self.statusBar().showMessage(f"Saving results to: {self.results_path}")

    # ---- Video setting ----
    def apply_video_mode(self):
        """Always on / always off override the difficulty-based behaviour."""
        if not self.pool:
            return
        level = self.pool[self.i].get("level", "intermediate")
        if self.video_setting == "half":    # on-vs-off test: one half on, the other off (random order)
            on_now = self._in_first_half(self.i) == (self.half_order == "on_first")
            mode = "video" if on_now else "off"
        else:
            mode = {"on": "video", "off": "off"}.get(self.video_setting) or VIDEO_MODE[level]
        self.video.set_mode(mode)

    def _half_message(self):
        first, second = ("ON", "OFF") if self.half_order == "on_first" else ("OFF", "ON")
        return f"Random order for this session: video {first} for the first half, then {second}."

    def _in_first_half(self, i):
        return i < (len(self.pool) + 1) // 2

    def set_balance(self, checked):
        self.balance_levels = checked
        self.statusBar().showMessage("Question mix will change the next time you restart the session.")

    def set_hold_hard(self, checked):
        self.hold_hard_late = checked
        self.statusBar().showMessage("Hard-question ordering will change the next time you restart the session.")

    def set_video_setting(self, key):
        self.video_setting = key
        self.video.show_setting(key)           # on-screen buttons
        if key in self.video_actions:          # menu
            self.video_actions[key].setChecked(True)
        self.apply_video_mode()
        if key == "half":
            self.statusBar().showMessage(self._half_message())

    # ---- Misc ----
    def toggle_video(self):
        self.video.setVisible(not self.video.isVisible())

    def load_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load questions", "", "JSON files (*.json)")
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            for q in data:
                assert {"section", "prompt", "choices", "answer"} <= q.keys()
                assert q.get("level", "intermediate") in VIDEO_MODE, "level must be easy, intermediate or hard"
                assert 2 <= len(q["choices"]) <= 4 and 0 <= q["answer"] < len(q["choices"])
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(self, "Couldn't load file",
                                f"Expected a list of question objects.\n\n{e}")
            return
        self.all_questions = data
        self.refresh_sections()
        self.start_session()


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
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

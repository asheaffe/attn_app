"""
SAT Practice + floating YouTube player

Install:   pip install PyQt6 PyQt6-WebEngine
Run:       python sat_app.py

- Main window: SAT-style multiple-choice practice (Math + Reading & Writing),
  plus much easier 'Easy Math' and 'Easy Reading & Writing' warm-up sections.
- A small YouTube player is embedded in the bottom-right corner of the main window.
  Paste any YouTube link (video, youtu.be, shorts, or playlist) and press Play.
- File > Load questions (JSON)... lets you add your own questions.
  Format: a list of objects like
    {"section": "Math", "passage": "(optional)", "prompt": "...",
     "choices": ["a", "b", "c", "d"], "answer": 0, "explanation": "..."}
  where "answer" is the 0-based index of the correct choice.
"""

import json
import random
import re
import sys

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QAction, QColor, QKeySequence, QPalette, QShortcut
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QApplication, QButtonGroup, QComboBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QPushButton, QRadioButton,
    QVBoxLayout, QWidget,
)

# --------------------------------------------------------------------------
# Question bank (original practice questions)
# --------------------------------------------------------------------------
QUESTIONS = [
    # ---- Math ----
    {"section": "Math",
     "prompt": "If 3x + 7 = 25, what is the value of 6x + 5?",
     "choices": ["31", "36", "41", "47"], "answer": 2,
     "explanation": "3x = 18, so 6x = 36 and 6x + 5 = 41."},
    {"section": "Math",
     "prompt": "A line passes through the points (2, 5) and (6, 13). What is the y-intercept of the line?",
     "choices": ["0", "1", "2", "3"], "answer": 1,
     "explanation": "Slope = (13 - 5)/(6 - 2) = 2. Using (2, 5): 5 = 2(2) + b, so b = 1."},
    {"section": "Math",
     "prompt": "What is the sum of the solutions to x² − 5x − 14 = 0?",
     "choices": ["−7", "−5", "5", "14"], "answer": 2,
     "explanation": "Factor: (x − 7)(x + 2) = 0, so x = 7 or x = −2. The sum is 5 (also −b/a = 5)."},
    {"section": "Math",
     "prompt": "Notebooks cost $4 each and pens cost $1.50 each. Maria buys 5 notebooks and some pens "
               "for a total of $29. How many pens did she buy?",
     "choices": ["4", "5", "6", "8"], "answer": 2,
     "explanation": "5 notebooks cost $20, leaving $9. $9 ÷ $1.50 = 6 pens."},
    {"section": "Math",
     "prompt": "After a 20% increase, the price of a jacket is $90. What was the original price?",
     "choices": ["$70", "$72", "$75", "$78"], "answer": 2,
     "explanation": "Original × 1.20 = 90, so the original price is 90 ÷ 1.2 = $75."},
    {"section": "Math",
     "prompt": "A circle has an area of 49π. What is its circumference?",
     "choices": ["7π", "14π", "49π", "98π"], "answer": 1,
     "explanation": "πr² = 49π gives r = 7, so the circumference is 2πr = 14π."},
    {"section": "Math",
     "prompt": "The mean of five numbers is 12. Four of the numbers are 8, 10, 14, and 15. What is the fifth number?",
     "choices": ["11", "12", "13", "15"], "answer": 2,
     "explanation": "The total must be 5 × 12 = 60. The four known numbers sum to 47, so the fifth is 13."},

    # ---- Reading & Writing ----
    {"section": "Reading & Writing",
     "prompt": "Which choice completes the text so that it conforms to the conventions of Standard English?\n\n"
               "The committee, along with several outside advisors, ______ expected to announce its decision on Friday.",
     "choices": ["are", "is", "were", "have been"], "answer": 1,
     "explanation": "The subject is 'The committee' (singular). 'Along with several outside advisors' is "
                    "parenthetical and doesn't change the number, so the verb is 'is'."},
    {"section": "Reading & Writing",
     "prompt": "Which choice completes the text with the most logical and precise word?\n\n"
               "The scientist's explanation was ______; even readers with no background in physics could follow it.",
     "choices": ["lucid", "ornate", "tentative", "elusive"], "answer": 0,
     "explanation": "The clause after the semicolon says anyone could follow it, so the explanation was clear: 'lucid'."},
    {"section": "Reading & Writing",
     "prompt": "Which choice completes the text with the most logical transition?\n\n"
               "Many cities have added protected bike lanes to reduce traffic congestion. ______ studies suggest "
               "the lanes also improve safety for pedestrians.",
     "choices": ["However,", "Instead,", "Moreover,", "Otherwise,"], "answer": 2,
     "explanation": "The second sentence adds another benefit rather than contrasting, so 'Moreover' fits."},
    {"section": "Reading & Writing",
     "prompt": "Which choice is a complete, correctly punctuated sentence?",
     "choices": ["The experiment failed, the team revised its method.",
                 "The experiment failed; so the team revised its method.",
                 "The experiment failed, so the team revised its method.",
                 "The experiment failed so, the team revised its method."], "answer": 2,
     "explanation": "Two independent clauses joined by 'so' need a comma before the conjunction. "
                    "A comma alone is a comma splice, and a semicolon shouldn't precede 'so'."},
    {"section": "Reading & Writing",
     "passage": "When engineers first proposed using drones to survey remote wetlands, many ecologists were "
                "skeptical, worried that the noise would disturb nesting birds. But field tests showed that at "
                "altitudes above 60 meters the birds' behavior was essentially unchanged, and the drones "
                "collected data far faster than researchers on foot.",
     "prompt": "Which choice best states the main idea of the text?",
     "choices": ["Drones are too noisy to be used in ecological research.",
                 "Despite early concerns, drones proved to be an effective and minimally disruptive survey tool.",
                 "Researchers on foot gather more accurate data than drones do.",
                 "Nesting birds are unaffected by any kind of human activity."], "answer": 1,
     "explanation": "The text moves from an initial worry to test results showing little disturbance and faster "
                    "data collection. Choice B captures both parts."},

    # ---- Easy warm-ups: Math ----
    {"section": "Easy Math",
     "prompt": "What is the value of 8 + 5 × 2?",
     "choices": ["16", "18", "20", "26"], "answer": 1,
     "explanation": "Multiply before adding: 5 × 2 = 10, and 8 + 10 = 18."},
    {"section": "Easy Math",
     "prompt": "What is 25% of 80?",
     "choices": ["15", "20", "25", "40"], "answer": 1,
     "explanation": "25% is one quarter, and 80 ÷ 4 = 20."},
    {"section": "Easy Math",
     "prompt": "If x + 9 = 15, what is the value of x?",
     "choices": ["5", "6", "7", "24"], "answer": 1,
     "explanation": "Subtract 9 from both sides: x = 15 − 9 = 6."},
    {"section": "Easy Math",
     "prompt": "A rectangle is 8 units long and 3 units wide. What is its area?",
     "choices": ["11", "22", "24", "32"], "answer": 2,
     "explanation": "Area = length × width = 8 × 3 = 24."},
    {"section": "Easy Math",
     "prompt": "Which of these numbers is the greatest?",
     "choices": ["0.5", "0.45", "0.6", "0.09"], "answer": 2,
     "explanation": "Compare tenths first: 0.6 has 6 tenths, more than any of the others."},
    {"section": "Easy Math",
     "prompt": "A pencil costs $0.50. How much do 6 pencils cost?",
     "choices": ["$2.50", "$3.00", "$3.50", "$4.00"], "answer": 1,
     "explanation": "6 × $0.50 = $3.00."},
    {"section": "Easy Math",
     "prompt": "What is the average (mean) of 4, 6, and 8?",
     "choices": ["5", "6", "7", "8"], "answer": 1,
     "explanation": "Add them: 4 + 6 + 8 = 18. Then divide by 3: 18 ÷ 3 = 6."},
    {"section": "Easy Math",
     "prompt": "If 2x = 14, what is the value of x?",
     "choices": ["5", "7", "12", "28"], "answer": 1,
     "explanation": "Divide both sides by 2: x = 14 ÷ 2 = 7."},

    # ---- Easy warm-ups: Reading & Writing ----
    {"section": "Easy Reading & Writing",
     "prompt": "Which choice completes the sentence correctly?\n\nShe ______ to school every day.",
     "choices": ["go", "goes", "going", "gone"], "answer": 1,
     "explanation": "'She' is singular, so the present-tense verb takes an -s: 'goes'."},
    {"section": "Easy Reading & Writing",
     "prompt": "Which word is closest in meaning to 'enormous'?",
     "choices": ["tiny", "huge", "quiet", "quick"], "answer": 1,
     "explanation": "'Enormous' means very large, which is 'huge'."},
    {"section": "Easy Reading & Writing",
     "prompt": "Which choice completes the text with the most logical transition?\n\n"
               "It was raining hard. ______ we brought umbrellas.",
     "choices": ["However,", "Therefore,", "For example,", "Likewise,"], "answer": 1,
     "explanation": "The umbrellas are a result of the rain, so 'Therefore' fits."},
    {"section": "Easy Reading & Writing",
     "prompt": "Which choice correctly completes the sentence?\n\nThe ______ toys were scattered across the floor.",
     "choices": ["childrens", "children's", "childrens'", "childrens's"], "answer": 1,
     "explanation": "'Children' is already plural, so the possessive adds apostrophe + s: 'children's'."},
    {"section": "Easy Reading & Writing",
     "passage": "Bees collect nectar from flowers to make honey. While they do this, pollen sticks to their "
                "bodies and is carried to other flowers, which helps plants make seeds.",
     "prompt": "According to the text, how do bees help plants?",
     "choices": ["By eating their leaves", "By carrying pollen from flower to flower",
                 "By digging up the soil", "By blocking the sunlight"], "answer": 1,
     "explanation": "The text says pollen sticks to bees and is carried to other flowers, helping plants make seeds."},
]

LETTERS = "ABCD"

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


class VideoPanel(QWidget):
    """Small YouTube player embedded in the main window (bottom-right)."""

    def __init__(self):
        super().__init__()
        self.setObjectName("videoPanel")
        self.setFixedSize(420, 320)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste a YouTube link…")
        self.url_input.returnPressed.connect(self.play)
        play_btn = QPushButton("Play")
        play_btn.clicked.connect(self.play)
        stop_btn = QPushButton("Stop")
        stop_btn.clicked.connect(self.stop)

        bar = QHBoxLayout()
        bar.addWidget(self.url_input, 1)
        bar.addWidget(play_btn)
        bar.addWidget(stop_btn)

        self.view = QWebEngineView()
        self.view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)
        self.view.settings().setAttribute(
            QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        self.view.page().fullScreenRequested.connect(lambda req: req.reject())
        self.stop()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(QLabel("YouTube player"))
        layout.addLayout(bar)
        layout.addWidget(self.view, 1)

    def play(self):
        src = youtube_embed_url(self.url_input.text())
        if not src:
            self.show_message("That doesn't look like a YouTube link.")
            return
        html = (
            '<html><body style="margin:0;background:#000">'
            f'<iframe src="{src}" style="position:absolute;inset:0;width:100%;height:100%;border:0" '
            'allow="autoplay; encrypted-media; picture-in-picture" '
            'referrerpolicy="strict-origin-when-cross-origin"></iframe></body></html>'
        )
        # A real-looking base URL gives YouTube the origin/referrer it wants for embeds.
        self.view.setHtml(html, QUrl("https://localhost/"))

    def stop(self):
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
"""


class SatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.video = VideoPanel()
        self.all_questions = list(QUESTIONS)
        self.pool, self.results, self.i = [], {}, 0

        self.setWindowTitle("SAT Practice")
        self.resize(1000, 720)
        self.setStyleSheet(STYLE)
        self._build_ui()
        self._build_menu()
        self.start_session()

    # ---- UI ----
    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        v = QVBoxLayout(root)
        v.setContentsMargins(28, 20, 28, 20)
        v.setSpacing(12)

        top = QHBoxLayout()
        self.section_box = QComboBox()
        self.section_box.currentIndexChanged.connect(self.start_session)
        self.meta = QLabel(objectName="meta")
        self.video_btn = QPushButton("Show / hide video")
        self.video_btn.clicked.connect(self.toggle_video)
        top.addWidget(QLabel("Section:"))
        top.addWidget(self.section_box)
        top.addStretch(1)
        top.addWidget(self.meta)
        top.addWidget(self.video_btn)
        v.addLayout(top)

        self.passage = QLabel(objectName="passage")
        self.passage.setWordWrap(True)
        self.prompt = QLabel(objectName="prompt")
        self.prompt.setWordWrap(True)
        v.addWidget(self.passage)
        v.addWidget(self.prompt)

        self.group = QButtonGroup(self)
        self.radios = []
        for k in range(4):
            r = QRadioButton()
            self.group.addButton(r, k)
            self.radios.append(r)
            v.addWidget(r)

        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        self.feedback.setStyleSheet("font-size: 15px; color: #000;")
        v.addWidget(self.feedback)
        v.addStretch(1)

        # Bottom row: navigation buttons on the left, embedded video on the right.
        bottom = QHBoxLayout()
        btns = QHBoxLayout()
        self.prev_btn = QPushButton("← Previous")
        self.submit_btn = QPushButton("Submit", objectName="primary")
        self.next_btn = QPushButton("Next →")
        self.restart_btn = QPushButton("Restart / reshuffle")
        self.prev_btn.clicked.connect(lambda: self.go(-1))
        self.next_btn.clicked.connect(lambda: self.go(+1))
        self.submit_btn.clicked.connect(self.submit)
        self.restart_btn.clicked.connect(self.start_session)
        for b in (self.prev_btn, self.submit_btn, self.next_btn, self.restart_btn):
            btns.addWidget(b)
        btns.addStretch(1)
        left = QVBoxLayout()
        left.addStretch(1)
        left.addLayout(btns)
        bottom.addLayout(left, 1)
        bottom.addWidget(self.video, 0, Qt.AlignmentFlag.AlignBottom)
        v.addLayout(bottom)

        # Keyboard shortcuts: A-D choose, Enter submits, arrows navigate
        for k, key in enumerate("ABCD"):
            QShortcut(QKeySequence(key), self, activated=lambda k=k: self._pick(k))
        QShortcut(QKeySequence(Qt.Key.Key_Return), self, activated=self.submit)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, activated=lambda: self.go(+1))
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, activated=lambda: self.go(-1))

    def _build_menu(self):
        act = QAction("Load questions (JSON)…", self)
        act.triggered.connect(self.load_json)
        self.menuBar().addMenu("&File").addAction(act)

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
        qs = [dict(q) for q in self.all_questions if sec in ("All", q["section"])]
        random.shuffle(qs)
        for q in qs:  # shuffle answer order, remembering the mapping
            q["order"] = random.sample(range(len(q["choices"])), len(q["choices"]))
        self.pool, self.results, self.i = qs, {}, 0
        self.show_question()

    def show_question(self):
        if not self.pool:
            self.prompt.setText("No questions in this section.")
            return
        q = self.pool[self.i]
        self.passage.setVisible(bool(q.get("passage")))
        self.passage.setText(q.get("passage", ""))
        self.prompt.setText(q["prompt"])

        self.group.setExclusive(False)
        for k, r in enumerate(self.radios):
            r.setChecked(False)
            if k < len(q["order"]):
                r.setText(f"{LETTERS[k]})   {q['choices'][q['order'][k]]}")
                r.setVisible(True)
            else:
                r.setVisible(False)
        self.group.setExclusive(True)

        self.feedback.clear()
        answered = self.i in self.results
        for r in self.radios:
            r.setEnabled(not answered)
        self.submit_btn.setEnabled(not answered)
        if answered:
            self.radios[self.results[self.i]].setChecked(True)
            self.show_feedback(q, self.results[self.i])
        self.prev_btn.setEnabled(self.i > 0)
        self.next_btn.setEnabled(self.i < len(self.pool) - 1)
        self.update_meta()

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
        self.results[self.i] = chosen
        for r in self.radios:
            r.setEnabled(False)
        self.submit_btn.setEnabled(False)
        self.show_feedback(self.pool[self.i], chosen)
        self.update_meta()

    def show_feedback(self, q, chosen):
        correct_pos = q["order"].index(q["answer"])
        if chosen == correct_pos:
            head = "<b>✓ Correct!</b>"
        else:
            head = (f"<b>✗ Incorrect.</b> "
                    f"The correct answer is <b>{LETTERS[correct_pos]}</b>.")
        self.feedback.setText(f"{head}<br>{q.get('explanation', '')}")

    def go(self, step):
        if self.pool and 0 <= self.i + step < len(self.pool):
            self.i += step
            self.show_question()

    def update_meta(self):
        right = sum(1 for i, c in self.results.items()
                    if c == self.pool[i]["order"].index(self.pool[i]["answer"]))
        self.meta.setText(f"Question {self.i + 1} of {len(self.pool)}   |   "
                          f"Score: {right}/{len(self.results)}")

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
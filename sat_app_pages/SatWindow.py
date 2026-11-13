import csv
import json
import os
import random
import time

from datetime import datetime
from pathlib import Path

from sat_app_pages.VideoPanel import VideoPanel
from sat_app_pages.LatexWidget import LatexWidget
from sat_app_pages.ReadyDialog import ReadyDialog

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QGuiApplication, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QButtonGroup, QFileDialog, QHBoxLayout, QLabel, QDialog,
    QMainWindow, QMessageBox, QPushButton, QRadioButton,
    QSplitter, QVBoxLayout, QWidget, QSizePolicy, QScrollArea
)

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

BASE_DIR = Path(__file__).resolve().parent.parent

DIFFICULTY_MAP = {
    "easy": "easy",
    "medium": "intermediate",
    "intermediate": "intermediate",
    "hard": "hard"
}

ANSWER_MAP = {"A": 0, "B": 1, "C": 2, "D": 3}

LETTERS = "ABCD"
QUESTIONS = load_questions(BASE_DIR / "data-files" / "opensat_questions.json")
TRAINING_QUESTIONS = load_questions(BASE_DIR / "data-files" / "training_questions.json")

CSV_FIELDS = ["timestamp", "session_id", "question_number", "session_half", "section", "level", "question",
              "chosen_answer", "correct_answer", "correct", "seconds_to_answer",
              "video_setting", "condition_order", "video_on", "video_loaded", "video_mode"]

class SatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.all_questions = list(QUESTIONS)
        self.training_questions = list(TRAINING_QUESTIONS)
        self.pool = []
        self.results = {} 
        self.i = 0

        # start in training mode
        self.training_mode = True
        self.experiment_started = False

        self.video_actions = {}
        self.video_setting = "half"
        
        self._checked_path = None
                  # "on_first" | "off_first" (re-randomized every session)
        self.results_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"data-files/sat_results.csv")
        self.session_id = ""
        self.q_elapsed, self.q_shown_at = {}, None   # per-question time on screen (seconds)
        self._warned_csv = False

        self.elapsed_seconds = 0

        # timer for each question
        self.timer = QTimer(self)
        self.timer.setInterval(1000)    # updates every second
        #self.timer.timeout.connect(self.update_countdown)

        ## SET THE TIME LIMIT PER QUESTION ##
        self.question_time_limit = 120
        self.time_remaining = self.question_time_limit

        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(1000)  # updates every second
        self.countdown_timer.timeout.connect(self.update_countdown)

        self.setWindowTitle("SAT Media-Multitasking")
        geo = QGuiApplication.primaryScreen().availableGeometry()
        self.resize(min(geo.width(), 1500), min(geo.height(), 860))
        self.setStyleSheet(STYLE)

    # ---- UI ----
    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        v = QVBoxLayout(root)
        v.setContentsMargins(28, 20, 28, 20)
        v.setSpacing(12)

        top = QHBoxLayout()

        self.timer_label = QLabel("Time Remaining for question: 02:00")

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

        top.addStretch(1)
        top.addWidget(self.timer_label)

        self.meta = QLabel(objectName="meta")
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
        
        question_layout.addWidget(self.passage)
        question_layout.addWidget(self.prompt)

        self.group = QButtonGroup(self)
        self.radios = []
        self.choice_labels = []

        for k in range(4):
            r = QRadioButton()
            label = LatexWidget()

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
        self.feedback.setStyleSheet("font-size: 15px; color: #000;")
        question_layout.addWidget(self.feedback)
        question_layout.addStretch(1)

        question_scroll.setWidget(question_content)
        v.addWidget(question_scroll, 1)

        btns = QHBoxLayout()

        self.next_btn = QPushButton("Submit", objectName="primary")

        self.next_btn.clicked.connect(self.handle_submit_next)
        
        btns.addWidget(self.next_btn)
        btns.addStretch(1)
        v.addLayout(btns)

        # allows the question panel to shrink independently of its content
        root.setMinimumWidth(0)
        root.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Expanding
        )

        # side-by-side
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        self.splitter.addWidget(root)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

        # start at approx 50/50 split
        self.splitter.setSizes([700, 700])

        self.splitter.setChildrenCollapsible(False)

        # Give both panels min usable width
        root.setMinimumWidth(300)

        self.setCentralWidget(self.splitter)

        # Keyboard shortcuts: A-D choose, Enter submits, arrows navigate
        for k, key in enumerate("ABCD"):
            QShortcut(QKeySequence(key), self, activated=lambda k=k: self._pick(k))
        QShortcut(QKeySequence(Qt.Key.Key_Return), self, activated=self.submit)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, activated=lambda: self.go(+1))
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, activated=lambda: self.go(-1))

    def start_training(self):
        # use the training questions
        #self.pool = list(self.training_questions)
        self.i = 0
        self.results = {}

        self._build_ui()
        self._build_menu()

        # start the session
        self.start_session()
    
    def start_experiment(self):
        # starts the session
        self._build_ui()
        self._build_menu()
        self.start_session()

        # initialize the videopanel mode with the current mode setting
        self.video = VideoPanel(self.apply_video_mode())

        # allow the video panel to occupy the right side of the screen
        self.video.setMinimumWidth(0)
        self.video.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.video.setMinimumWidth(300)

        self.splitter.addWidget(self.video)

        self.video.play()
   
    def finish_training(self):
        self._stop_timer()
        self.training_mode = False

        # reset question count vars
        self.i = 0
        self.results = {}

        # show ready dialog again
        dialog = ReadyDialog(self, training=False)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.start_experiment()
        else:
            self.close()

    def handle_submit_next(self):
        answered = self.i in self.results

        if answered:
            if self.i < len(self.pool) - 1:
                
                self.feedback.clear()
                self.go(+1)

            else:
                self.finish_training()

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

        session_menu = self.menuBar().addMenu("&Session")
        # hold = QAction("Hold hard questions until the second half", self)
        # hold.setCheckable(True)
        # hold.setChecked(self.hold_hard_late)
        # hold.triggered.connect(self.set_hold_hard)
        # session_menu.addAction(hold)

        self.statusBar().showMessage(f"Saving results to: {self.results_path}")

    def start_session(self):
        if not self.training_mode:

            lvl = "all"     # TODO: this is hard-coded for now lolololol
            qs = [dict(q) for q in self.all_questions
                if lvl in ("all", q.get("level", "intermediate"))]
            
            # Equal numbers per level: draw as many from each level as the smallest level has.
            by_level = {
                level: [q for q in qs if q.get("level", "intermediate") == level]
                for level in ("easy", "intermediate", "hard")
            }

            # 30 questions total
            ### TODO: this is hard-coded, will want to set to change on input later ###
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
            qs = TRAINING_QUESTIONS

        random.shuffle(qs)

        self.elapsed_seconds = 0
        #self.timer_label.setText("Time: 00:00")
        self.timer.timeout.connect(self.update_countdown)

        for q in qs:  # shuffle answer order, remembering the mapping
            q["order"] = random.sample(range(len(q["choices"])), len(q["choices"]))
        self.pool, self.results, self.i = qs, {}, 0
        self.q_elapsed, self.q_shown_at = {}, None
        self.session_id = datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{random.randrange(16 ** 3):03x}"
        self.half_order = random.choice(("on_first", "off_first"))   # randomize the on/off test order
        self.show_question()

    def show_question(self):
        if not self.pool:
            self.prompt.setText("No questions in this section.")
            return
        q = self.pool[self.i]

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

        answered = self.i in self.results

        for r in self.radios:
            r.setEnabled(not answered)

        if answered:
            chosen = self.results[self.i]

            # restore previously selected answer
            self.radios[chosen].setChecked(True)

            # display feedback during training
            if self.training_mode:
                self.show_feedback(q, chosen)

        else:
            # question hasn't been answered
            self.next_btn.setText("Submit")

        #self.prev_btn.setEnabled(self.i > 0)

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
        
        # stop the timer and record answer
        self._stop_timer()
        self.results[self.i] = chosen

        # disables answer choices
        for r in self.radios:
            r.setEnabled(False)

        # update progress
        self.update_meta()

        if self.training_mode:
            # show feedback and wait for next only in training
            self.show_feedback(self.pool[self.i], chosen)
            self.log_answer(self.pool[self.i], chosen)

            self.next_btn.setText("Next")
            self.next_btn.setEnabled(True)
        
        else:
            # log answer and immediately advance without feedback during experiment
            self.log_answer(self.pool[self.i], chosen)

            self.feedback.clear()
            self.go(1)

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
        self.meta.setText(f"Question {self.i + 1} of {len(self.pool)}")

    # ---- Timing + CSV results ----
    def _start_timer(self):
        """Start timing the question on screen (answered questions aren't timed again)."""
        self.countdown_timer.stop()

        self.time_remaining = self.question_time_limit

        self.timer_label.setText("Time Remaining: 02:00")
        self.timer_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: black;"
        )
        self.countdown_timer.start()
        
        self.q_shown_at = None if self.i in self.results else time.monotonic()

    def _stop_timer(self):
        """Add the time since the question appeared; time spent on other questions isn't counted."""
        if self.q_shown_at is not None:
            self.q_elapsed[self.i] = self.q_elapsed.get(self.i, 0.0) + (time.monotonic() - self.q_shown_at)
            self.q_shown_at = None

    def update_countdown(self):
        self.time_remaining -= 1

        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60

        self.timer_label.setText(
            f"Time Remaining: {minutes:02d}:{seconds:02d}"
        )

        if self.time_remaining <= 10:
            self.timer_label.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: red;"
            )

        if self.time_remaining <= 0:
            self.countdown_timer.stop()
            self.time_remaining = 0
            self.handle_timeout()

    def handle_timeout(self):
        if not self.pool or self.i in self.results:
            return
        
        # -1 represents no answer
        chosen = -1

        self._stop_timer()
        self.results[self.i] = chosen

        for r in self.radios:
            r.setEnabled(False)

        self.next_btn.setEnabled(False)

        if self.training_mode:
            self.show_feedback(self.pool[self.i], chosen)
            
        self.update_meta()
        self.log_answer(self.pool[self.i], chosen)

        # automatically advance to the next question
        QTimer.singleShot(1000, lambda: self.go(+1))

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
            #"video_setting": VIDEO_SETTINGS[self.video_setting],
            "condition_order": False if self.training_mode else         # ik this is ugly im sorry
                ("on_then_off" if self.i < len(self.pool)/2 and self.video.mode == "video" else "off_then_on"),
            "video_on": False if self.training_mode else int(self.video.mode == "video"),      # 1 = picture playing, 0 = off / paused / audio only
            "video_loaded": False if self.training_mode else int(self.video.has_video),        # 0 = no YouTube link had been loaded yet
            "video_mode": "training" if self.training_mode else self.video.mode,                    # video | audio (audio only) | pause | off
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
        """Assigns an initial value for the video being on/off based on self.video_setting
        
        :return: str mode setting in "video", "off" """
        if self.training_mode:
            mode = "off"
            return
        
        mode = ""

        if self.video_setting == "half":    # on-vs-off test: one half on, the other off (random order)
            on_now = random.choice([0, 1]) 
            mode = "video" if on_now else "off"
        else:
            mode = {"on": "video", "off": "off"}.get(self.video_setting)
        print(on_now)
        return mode
 
    def _in_first_half(self, i):
        return i < (len(self.pool) + 1) // 2

    # def set_hold_hard(self, checked):
    #     self.hold_hard_late = checked
    #     self.statusBar().showMessage("Hard-question ordering will change the next time you restart the session.")

    def set_video_setting(self, key):
        self.video_setting = key
        #self.video.show_setting(key)           # on-screen buttons
        if key in self.video_actions:          # menu
            self.video_actions[key].setChecked(True)
        self.apply_video_mode()

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
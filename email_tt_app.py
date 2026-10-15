"""
Inbox + Shorts

Install:   pip install PyQt6
Run:       python inbox_shorts_app.py

- A scrollable inbox of sample emails (click one to read it).
- After every few emails, a row of static, eye-catching TikTok-style thumbnails.
  Clicking a thumbnail opens its link in your default browser.

Customize the shorts (optional): put a file named shorts.json next to this script:
  [
    {"title": "30-second pasta hack", "creator": "@cookwithmaya", "views": "2.4M",
     "url": "https://www.tiktok.com/@cookwithmaya/video/123...",
     "image": "C:/path/to/thumbnail.jpg"}          <- "image" is optional
  ]
Without "image", a colorful thumbnail is drawn for you.
"""

import json
import os
import random
import sys

from PyQt6.QtCore import QPointF, QRectF, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import (QBrush, QColor, QDesktopServices, QFont, QLinearGradient,
                         QPainter, QPainterPath, QPalette, QPixmap, QPolygonF)
from PyQt6.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout, QLabel,
                             QMainWindow, QPushButton, QScrollArea, QVBoxLayout,
                             QWidget)

EMAILS_PER_SHORTS_ROW = 4   # a row of shorts appears after this many emails
THUMBS_PER_ROW = 5
THUMB_W, THUMB_H = 150, 266  # 9:16

# --------------------------------------------------------------------------
# Sample data
# --------------------------------------------------------------------------
DEFAULT_SHORTS = [
    {"title": "You won't believe what happens at the end 😱", "creator": "@plotTwistPete", "views": "4.1M"},
    {"title": "This 30-second hack saves me 2 hours a day", "creator": "@lifehackLena", "views": "2.4M"},
    {"title": "POV: it's Monday and your inbox is full", "creator": "@officeVibes", "views": "890K"},
    {"title": "Pasta so good the internet broke 🍝", "creator": "@cookwithmaya", "views": "6.7M"},
    {"title": "Wait for it... 👀", "creator": "@waitforit", "views": "3.3M"},
    {"title": "My cat vs. a cucumber (round 2)", "creator": "@catsofinsta", "views": "12M"},
    {"title": "Satisfying cleanup compilation ✨", "creator": "@cleanqueen", "views": "1.9M"},
    {"title": "I learned guitar in 7 days. Here's how", "creator": "@strumsteve", "views": "1.2M"},
    {"title": "Things I wish I knew before college", "creator": "@campusclara", "views": "760K"},
    {"title": "Rate my desk setup 1-10 🖥️", "creator": "@deskgoals", "views": "540K"},
]
DEFAULT_URL = "https://www.tiktok.com/"

PALETTES = [("#ff6b81", "#7b2ff7"), ("#00c6ff", "#0072ff"), ("#f7971e", "#ffd200"),
            ("#43e97b", "#38b2ac"), ("#fa709a", "#fee140"), ("#a18cd1", "#fbc2eb"),
            ("#ff9a9e", "#fad0c4"), ("#30cfd0", "#330867")]

EMAIL_TEMPLATES = [
    ("Priya Nair", "Q4 planning: agenda attached",
     "Hi all, attached is the agenda for Thursday's planning session. Please add any topics by end of day Wednesday so we can keep the meeting to 45 minutes."),
    ("Campus Bookstore", "Your order has shipped",
     "Good news! Your order #48213 is on its way. Estimated delivery is Friday. You can track the package using the link below."),
    ("Marcus Lee", "Re: lab report feedback",
     "Thanks for sending the draft. Overall it reads well. I'd tighten the methods section and add one more citation to the second paragraph of the discussion."),
    ("Library Services", "Reminder: 2 items due soon",
     "This is a friendly reminder that two of your borrowed items are due this week. You can renew them online from your account page."),
    ("Jenna Alvarez", "Dinner on Saturday?",
     "A few of us are thinking of trying that new ramen place around 7. Let me know if you're in and I'll make a reservation for the group."),
    ("StudyHub", "Your weekly progress summary",
     "You completed 5 practice sessions this week and improved your accuracy by 8%. Keep it up! Here's what we recommend focusing on next."),
    ("IT Help Desk", "Scheduled maintenance this weekend",
     "Email and file storage will be briefly unavailable Sunday between 2 and 4 AM while we apply updates. No action is needed on your part."),
    ("David Okafor", "Notes from today's meeting",
     "Great discussion today. Action items: Priya to share the budget draft, Sam to confirm the venue, and I'll send the revised timeline tomorrow."),
    ("Travel Desk", "Your itinerary for next month",
     "Your flight is confirmed. Check-in opens 24 hours before departure. Remember to bring a valid photo ID and arrive at least two hours early."),
    ("Sofia Martins", "Photos from the trip!",
     "Finally got around to sorting the pictures. I put everything in a shared album, so feel free to add your own favorites there too."),
    ("Payroll", "Your pay statement is ready",
     "Your latest pay statement is now available in the employee portal. Please review it and contact us if anything looks incorrect."),
    ("Tom Reyes", "Quick question about the schedule",
     "Do you know if the Tuesday session got moved to the afternoon? The calendar shows two different times and I want to make sure I'm not late."),
    ("Neighborhood Association", "Community cleanup day",
     "Join us this Saturday morning for our fall cleanup. Gloves and bags provided, and there will be coffee and donuts for all volunteers."),
    ("Aisha Khan", "Can you review my slides?",
     "I'm presenting on Friday and would love a second pair of eyes. Mostly worried about the flow of the middle section. No rush, tomorrow is fine."),
    ("Gym Membership", "We miss you!",
     "It's been a couple of weeks since your last visit. Come in this week for a free guest pass and a complimentary fitness check-in."),
    ("Ben Carter", "Re: group project split",
     "Sounds good to me. I'll take the data cleaning and first set of charts. Let's sync Thursday evening to merge everything before the deadline."),
]

TIME_LABELS = ["10:42 AM", "10:15 AM", "9:58 AM", "9:12 AM", "8:47 AM", "8:03 AM",
               "Yesterday", "Yesterday", "Yesterday", "Mon", "Mon", "Sun", "Sun", "Sat"]
AVATAR_COLORS = ["#ffd6e0", "#d6e9ff", "#fff1c1", "#d9f7e0", "#e8dcff", "#ffe0c7"]


def build_emails(n=40):
    rng = random.Random(7)
    emails = []
    for i in range(n):
        sender, subject, body = EMAIL_TEMPLATES[(i * 5 + rng.randint(0, 3)) % len(EMAIL_TEMPLATES)]
        when = TIME_LABELS[i] if i < len(TIME_LABELS) else f"Sep {max(1, 30 - (i - len(TIME_LABELS)))}"
        emails.append({"sender": sender, "subject": subject, "body": body,
                       "time": when, "unread": i < 20 and i % 3 != 2,
                       "color": AVATAR_COLORS[i % len(AVATAR_COLORS)]})
    return emails


def load_shorts():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shorts.json")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if data:
                return data
        except Exception as e:  # noqa: BLE001
            print("Couldn't read shorts.json, using defaults:", e)
    return DEFAULT_SHORTS


# --------------------------------------------------------------------------
# Thumbnail rendering (static images, no animation)
# --------------------------------------------------------------------------
def make_thumbnail(item, idx, w=THUMB_W, h=THUMB_H):
    pm = QPixmap(w, h)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    clip = QPainterPath()
    clip.addRoundedRect(QRectF(0, 0, w, h), 10, 10)
    p.setClipPath(clip)

    img_path = item.get("image")
    photo = QPixmap(img_path) if img_path and os.path.exists(img_path) else QPixmap()
    if not photo.isNull():
        photo = photo.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                             Qt.TransformationMode.SmoothTransformation)
        p.drawPixmap(-(photo.width() - w) // 2, -(photo.height() - h) // 2, photo)
    else:
        c1, c2 = PALETTES[idx % len(PALETTES)]
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0, QColor(c1))
        grad.setColorAt(1, QColor(c2))
        p.fillRect(0, 0, w, h, QBrush(grad))

    # Big play button
    cx, cy, r = w / 2, h * 0.40, 26
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255, 235))
    p.drawEllipse(QPointF(cx, cy), r, r)
    p.setBrush(QColor(20, 20, 20))
    p.drawPolygon(QPolygonF([QPointF(cx - 8, cy - 13), QPointF(cx - 8, cy + 13), QPointF(cx + 14, cy)]))

    # View-count badge (top-left)
    badge_font = QFont()
    badge_font.setPointSize(9)
    badge_font.setBold(True)
    p.setFont(badge_font)
    p.setBrush(QColor(255, 255, 255, 235))
    p.drawRoundedRect(QRectF(8, 8, 62, 22), 11, 11)
    p.setPen(QColor(0, 0, 0))
    p.drawText(QRectF(8, 8, 62, 22), Qt.AlignmentFlag.AlignCenter, f"▶ {item.get('views', '1M')}")

    # Caption strip (bottom)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255, 240))
    p.drawRect(QRectF(0, h - 72, w, 72))
    p.setPen(QColor(0, 0, 0))
    title_font = QFont()
    title_font.setPointSize(9)
    title_font.setBold(True)
    p.setFont(title_font)
    p.drawText(QRectF(8, h - 68, w - 16, 44),
               int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap),
               item.get("title", ""))
    small = QFont()
    small.setPointSize(8)
    p.setFont(small)
    p.drawText(QRectF(8, h - 22, w - 16, 18),
               int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
               item.get("creator", ""))
    p.end()
    return pm


# --------------------------------------------------------------------------
# Widgets
# --------------------------------------------------------------------------
class ClickableFrame(QFrame):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)


class EmailRow(ClickableFrame):
    def __init__(self, email, on_open):
        super().__init__()
        self.setObjectName("emailRow")
        self.email = email
        self.clicked.connect(lambda: on_open(self))

        avatar = QLabel(email["sender"][0])
        avatar.setFixedSize(42, 42)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"background:{email['color']}; border-radius:21px; font-size:17px; font-weight:bold;")

        self.sender = QLabel(email["sender"])
        self.time = QLabel(email["time"])
        self.subject = QLabel(email["subject"])
        preview = email["body"] if len(email["body"]) < 110 else email["body"][:107] + "…"
        self.preview = QLabel(preview)

        top = QHBoxLayout()
        top.addWidget(self.sender)
        top.addStretch(1)
        top.addWidget(self.time)
        text = QVBoxLayout()
        text.setSpacing(2)
        text.addLayout(top)
        text.addWidget(self.subject)
        text.addWidget(self.preview)

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 10, 16, 10)
        row.setSpacing(14)
        row.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)
        row.addLayout(text, 1)
        self.refresh()

    def refresh(self):
        weight = "bold" if self.email["unread"] else "normal"
        for lbl in (self.sender, self.subject):
            lbl.setStyleSheet(f"font-weight:{weight}; font-size:14px;")
        self.time.setStyleSheet(f"font-weight:{weight}; font-size:12px;")
        self.preview.setStyleSheet("font-size:13px;")


class ShortsRow(QFrame):
    def __init__(self, items, start_idx):
        super().__init__()
        self.setObjectName("shortsRow")
        header = QLabel("🔥 Trending shorts you might like")
        header.setStyleSheet("font-weight:bold; font-size:14px;")

        thumbs = QHBoxLayout()
        thumbs.setSpacing(12)
        for k, item in enumerate(items):
            t = ClickableLabel()
            t.setObjectName("thumb")
            t.setPixmap(make_thumbnail(item, start_idx + k))
            t.setFixedSize(THUMB_W + 4, THUMB_H + 4)
            t.setToolTip(f"{item.get('title', '')}  {item.get('creator', '')}")
            url = item.get("url", DEFAULT_URL)
            t.clicked.connect(lambda u=url: QDesktopServices.openUrl(QUrl(u)))
            thumbs.addWidget(t)
        thumbs.addStretch(1)

        v = QVBoxLayout(self)
        v.setContentsMargins(16, 12, 16, 14)
        v.setSpacing(10)
        v.addWidget(header)
        v.addLayout(thumbs)


class EmailDialog(QDialog):
    def __init__(self, email, parent=None):
        super().__init__(parent)
        self.setWindowTitle(email["subject"])
        self.setMinimumSize(520, 300)
        subject = QLabel(email["subject"])
        subject.setStyleSheet("font-size:18px; font-weight:bold;")
        subject.setWordWrap(True)
        meta = QLabel(f"From: {email['sender']}     {email['time']}")
        body = QLabel(email["body"])
        body.setWordWrap(True)
        body.setStyleSheet("font-size:15px;")
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        v = QVBoxLayout(self)
        v.setContentsMargins(24, 20, 24, 20)
        v.setSpacing(12)
        for w in (subject, meta, body):
            v.addWidget(w)
        v.addStretch(1)
        v.addWidget(close, 0, Qt.AlignmentFlag.AlignLeft)


STYLE = """
QWidget { color: #000000; }
QMainWindow, QScrollArea, QWidget#body, QDialog { background: #f5f6fa; }
QLabel#title { font-size: 20px; font-weight: bold; }
QFrame#emailRow { background: #ffffff; border-bottom: 1px solid #e1e4ee; }
QFrame#emailRow:hover { background: #eef1ff; }
QFrame#shortsRow { background: #fff6e5; border-top: 1px solid #f0d9a8; border-bottom: 1px solid #f0d9a8; }
QLabel#thumb { border: 2px solid transparent; border-radius: 12px; }
QLabel#thumb:hover { border: 2px solid #fe2c55; }
QPushButton { padding: 8px 18px; border-radius: 6px; border: 1px solid #c4c8d6; background: #ffffff; }
QPushButton:hover { background: #eef1ff; }
"""


class InboxWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inbox")
        self.resize(920, 760)

        title = QLabel("Inbox")
        title.setObjectName("title")
        title.setContentsMargins(16, 12, 16, 12)

        body = QWidget()
        body.setObjectName("body")
        col = QVBoxLayout(body)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)

        shorts = load_shorts()
        emails = build_emails()
        row_no = 0
        for n, email in enumerate(emails, start=1):
            col.addWidget(EmailRow(email, self.open_email))
            if n % EMAILS_PER_SHORTS_ROW == 0:
                start = (row_no * THUMBS_PER_ROW) % len(shorts)
                items = [shorts[(start + k) % len(shorts)] for k in range(THUMBS_PER_ROW)]
                col.addWidget(ShortsRow(items, start))
                row_no += 1
        col.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(body)

        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(title)
        outer.addWidget(scroll, 1)
        self.setCentralWidget(central)

    def open_email(self, row):
        row.email["unread"] = False
        row.refresh()
        EmailDialog(row.email, self).exec()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    pal = QPalette()  # force a light theme with black text
    for role, color in [
        (QPalette.ColorRole.Window, "#f5f6fa"), (QPalette.ColorRole.WindowText, "#000000"),
        (QPalette.ColorRole.Base, "#ffffff"), (QPalette.ColorRole.Text, "#000000"),
        (QPalette.ColorRole.Button, "#ffffff"), (QPalette.ColorRole.ButtonText, "#000000"),
        (QPalette.ColorRole.ToolTipBase, "#ffffff"), (QPalette.ColorRole.ToolTipText, "#000000"),
    ]:
        pal.setColor(role, QColor(color))
    app.setPalette(pal)
    app.setStyleSheet(STYLE)
    win = InboxWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
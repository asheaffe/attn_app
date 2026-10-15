"""
Inbox + Phone Notifications
---------------------------
An email client, loaded with emails already ranked by importance
(Critical > High > Medium > Low). Click one to read it; it opens on the left and
your reply shows up under it as an email thread.

Phone-style notifications pop up in the top-right corner one at a time:
each stays for 5 seconds, then there is a 3-second pause before the next one.
They look like social-media notifications (likes, new followers, viral videos, live
streams...). About 10% are catchy teasers that relate to the content of the emails
in the inbox (see RELATED_CHANCE); the rest are unrelated.

Write a reply in the box under each email and press Send to earn points
(Critical emails are worth the most, Low the least). Click a notification
to open a simulated Instagram/TikTok-style video (or an image for Buzz).

Standard library only (tkinter).  Run with:  python email_app.py
Text size: change FONT_SCALE below, press Ctrl + / Ctrl - / Ctrl 0 while the
app is running, or start with:  python email_app.py --scale 1.5
"""

import argparse
import math
import random
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path

# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------
FONT_SCALE = 1.2              # 1.0 = small, 1.5 = large, 2.0 = very large
DEFAULT_SCALE = FONT_SCALE
RELATED_CHANCE = 0.10         # chance a notification relates to an email's content
NOTIFICATION_SHOW_MS = 5000   # how long each notification stays on screen
NOTIFICATION_GAP_MS = 10000    # pause before the next notification appears
POINTS = {"Critical": 100, "High": 50, "Medium": 25, "Low": 10}   # reward per reply
MIN_REPLY_CHARS = 10          # a reply must be at least this long to count
PHOTOS_DIR = Path(__file__).resolve().parent / "media"
PHOTO_SUBFOLDERS = {"insta": "instagram", "tiktok": "tiktok"}

def F(family, size, *style):
    """Font tuple with the current FONT_SCALE applied."""
    return (family, max(1, round(size * FONT_SCALE)), *style)


# Importance levels: (minimum score, name, badge colour, row tint)
LEVELS = [
    (90, "Critical", "#c62828", "#fde4e4"),
    (70, "High",     "#e67700", "#fff0dc"),
    (40, "Medium",   "#8a6d00", "#fff9d6"),
    (0,  "Low",      "#6f6f6f", "#f3f3f3"),
]


def level_of(score):
    for minimum, name, colour, tint in LEVELS:
        if score >= minimum:
            return name, colour, tint


# ---------------------------------------------------------------------------
# EMAILS  (sender, address, subject, received, importance score 0-100, body,
#          catchy notification title that teases this email)
# ---------------------------------------------------------------------------
_RAW_EMAILS = [
    ("Dana Whitfield", "dana.whitfield@northwind.example",
     "URGENT: Board deck needs your sign-off by 2 PM", "8:05 AM", 98,
     "Hi,\n\nThe board meets at 3 PM and I still need your approval on the final deck. "
     "Please review slides 4-9 (the revenue projections) and reply with your sign-off by "
     "2 PM today. If you have changes, call me directly rather than emailing.\n\nThanks,\nDana",
     "Your boss is typing... and it's about a 2 PM deadline"),
    ("IT Security", "security@northwind.example",
     "Action required: suspicious login to your account", "7:48 AM", 95,
     "We detected a sign-in to your account from an unrecognized device in another country "
     "at 6:52 AM.\n\nIf this was not you, reset your password immediately and contact the "
     "help desk at ext. 4400. If it was you, no action is needed.\n\n- IT Security",
     "Unknown device just logged in as you. Not a vibe."),
    ("Dr. Patel's Office", "frontdesk@patelfamilyhealth.example",
     "Your appointment has been moved to tomorrow at 8:30 AM", "Yesterday", 91,
     "Dr. Patel has had to reschedule. Your check-up is now tomorrow at 8:30 AM.\n\n"
     "Please arrive ten minutes early and bring your insurance card. Reply to confirm, or "
     "call the office if you need a different time.",
     "Plot twist: your appointment moved to tomorrow morning"),
    ("Marcus Lee (Client)", "marcus.lee@brightpath.example",
     "Contract revisions - please review today", "9:12 AM", 86,
     "Hello,\n\nOur legal team has marked up sections 3, 7 and 12 of the agreement. The "
     "payment terms are the main sticking point. Could you look over the changes today so "
     "we can keep the signing date on track?\n\nBest,\nMarcus",
     "The client left notes. So. Many. Notes."),
    ("Finance Department", "expenses@northwind.example",
     "Expense report rejected: missing receipt", "Yesterday", 78,
     "Your expense report #4471 could not be processed because the receipt for the $42.60 "
     "team lunch is missing. Please attach it and resubmit by Friday to be reimbursed in "
     "this pay cycle.",
     "Your missing lunch receipt is the talk of finance"),
    ("Hollis Property Management", "leasing@hollisproperties.example",
     "Lease renewal paperwork", "Mon", 74,
     "Your lease expires at the end of next month. The renewal documents are attached. "
     "Please sign and return them within 14 days to lock in the current rate; after that "
     "the rent will be adjusted.",
     "Your landlord wants you to sign something. Again."),
    ("Priya Nair", "priya.nair@northwind.example",
     "Can we move Thursday's 1:1?", "10:30 AM", 72,
     "Hey! Something came up on Thursday afternoon. Could we move our 1:1 to Friday at "
     "10 instead? Totally fine if not, I can also do Wednesday after 4.\n\nThanks!\nPriya",
     "Priya asked to move Thursday. Do we panic?"),
    ("Sprint Bot", "noreply@northwind.example",
     "Weekly sprint summary", "Mon", 58,
     "Sprint 42 summary:\n  - 14 tickets closed\n  - 3 tickets carried over\n  - 2 new bugs "
     "reported\n\nVelocity is up 6% compared to last sprint.",
     "Your sprint stats just dropped. You're trending!"),
    ("Sam Ortiz", "sam.ortiz@northwind.example",
     "Draft onboarding guide - feedback welcome", "Yesterday", 55,
     "I finished a first draft of the new-hire onboarding guide. No rush, but I'd love your "
     "thoughts on the structure and whether the tools section is too long.\n\nCheers,\nSam",
     "Sam wants your honest take on the onboarding guide"),
    ("Conference Committee", "register@devsummit.example",
     "Early-bird registration closes Friday", "Tue", 52,
     "Early-bird pricing for DevSummit ends this Friday at midnight. Register now to save "
     "$150 on a full-access pass. Group discounts are available for teams of five or more.",
     "Early-bird tickets are going fast. Are you in?"),
    ("Mom", "mom@familymail.example",
     "Dinner on Sunday?", "Yesterday", 48,
     "Hi sweetheart, are you free for dinner on Sunday? I'm making the lasagna you like. "
     "Let me know and whether you'll bring anyone. Love, Mom",
     "Mom asked about Sunday dinner. Reply before she calls."),
    ("City Library", "notices@citylibrary.example",
     "Reminder: 2 items due in 3 days", "Tue", 42,
     "The following items are due back in three days:\n  - A Field Guide to Backyard Birds\n"
     "  - The Art of Slow Cooking\n\nYou can renew online if no one else has placed a hold.",
     "Your library books are giving overdue energy"),
    ("Streamline Weekly", "news@streamlineweekly.example",
     "10 productivity hacks you'll actually use", "Mon", 30,
     "This week: batch your email, try the two-minute rule, and why a clean desk may not "
     "matter as much as you think. Read the full list on our site.",
     "10 hacks to change your Tuesday (number 7 is wild)"),
    ("ShopMart", "orders@shopmart.example",
     "Your order has shipped", "Tue", 28,
     "Good news! Your order #88213 has shipped and should arrive within 3-5 business days. "
     "You can track your package using the link in your account.",
     "Your package is on the move. Track it live!"),
    ("FitLife Gym", "hello@fitlifegym.example",
     "Class schedule for next month", "Mon", 22,
     "Our next-month class schedule is live. New this month: sunrise yoga, a 6 PM spin "
     "class on Wednesdays, and a beginners' strength workshop.",
     "New spin classes just dropped. Book before they fill up"),
    ("Maple Street Neighbors", "maple.street@neighborhood.example",
     "Block party planning thread", "Sun", 15,
     "We're collecting ideas for the block party! So far the debate is bounce house versus "
     "food trucks. Please reply-all with your vote (and please stop arguing about parking).",
     "The block party poll is getting heated"),
    ("DealDrop", "promo@dealdrop.example",
     "20% off everything this weekend only", "Sun", 8,
     "Everything is 20% off until Sunday midnight. Yes, everything. Use code WEEKEND20 at "
     "checkout. Unsubscribe at any time.",
     "Flash sale alert: 20% off everything this weekend"),
]
_KEYS = ("sender", "address", "subject", "time", "score", "body", "notif")
EMAILS = sorted((dict(zip(_KEYS, t)) for t in _RAW_EMAILS), key=lambda e: -e["score"])

# ---------------------------------------------------------------------------
# SOCIAL-MEDIA NOTIFICATIONS  (app, title, subtitle, image shown on click)
# Three made-up apps: Gramly (photos & stories), Clipt (short videos), Buzz (posts).
# ---------------------------------------------------------------------------
APP_COLORS = {"Gramly": "#e1306c", "Clipt": "#fe2c55", "Buzz": "#1d9bf0"}

GENERIC_NOTIFS = [
    # --- Gramly
    ("Gramly", "maya.codes and 23 others liked your photo", "Your post is on fire", "likes"),
    ("Gramly", "jordan_runs started following you", "Follow them back?", "follower"),
    ("Gramly", "sam.eats commented: okay this looks unreal", "Reply to sam.eats", "comment"),
    ("Gramly", "Your story has 312 views and climbing", "See who's watching", "story"),
    ("Gramly", "priya.travels is live right now. Join before it ends!", "Live now", "live"),
    ("Gramly", "You were tagged in a photo from last weekend", "Tap to see it (brace yourself)", "photo"),
    ("Gramly", "alex.snaps sent you a message", "did you see this??", "dm"),
    ("Gramly", "graham_smith wants you to see this!", "let them know you saw it", "influencer-img.png"),
    ("Gramly", "On this day: your most questionable haircut", "See your memory", "photo"),
    ("Gramly", "Your reel just passed 10K plays", "You're trending in your area", "trending"),
    ("Gramly", "dana_reads mentioned you in a comment", "See what she said", "mention"),
    ("Gramly", "You have 14 new followers today", "Main character energy", "follower"),
    ("Gramly", "5 friends posted since you last checked", "Don't miss out", "photo"),
    ("Gramly", "Your post is getting more likes than usual", "Post again while it's hot", "likes"),
    # --- Clipt
    ("Clipt", "Your video just hit 5,000 views", "Post another while you're hot", "views"),
    ("Clipt", "Your sound is being used in 40 new videos", "You started a trend", "sound"),
    ("Clipt", "dance.with.dee uploaded a new video", "Watch before it blows up", "clip"),
    ("Clipt", "This video is going viral right now. You have to see it.", "Trending in your feed", "trending"),
    ("Clipt", "mike.makes replied to your comment with a video", "Watch the reply", "comment"),
    ("Clipt", "You have a new duet request", "Tap to accept", "clip"),
    ("Clipt", "Go live now and your followers will be notified", "Don't keep them waiting", "live"),
    ("Clipt", "Your video was picked for the For You page", "Congrats, creator!", "trophy"),
    ("Clipt", "12 people liked your comment", "Keep the conversation going", "likes"),
    ("Clipt", "Your daily streak is about to expire", "Post today to keep it alive", "trending"),
    ("Clipt", "mike.makes sent you a video", "Watch it now", "dm"),
    ("Clipt", "Your video has 200 new comments", "See what people are saying", "comment"),
    # --- Buzz
    ("Buzz", "Your post is getting a lot of replies", "See what people are saying", "comment"),
    ("Buzz", "Trending near you: why is everyone talking about toast?", "Join the conversation", "trending"),
    ("Buzz", "jordan_lee reposted your post", "Your reach just doubled", "likes"),
    ("Buzz", "@casey.b mentioned you", "this is exactly what I meant", "mention"),
    ("Buzz", "You gained 50 new followers this week", "Your reach is up 38%", "follower"),
    ("Buzz", "Someone you follow is hosting a live audio room", "Join now", "live"),
    ("Buzz", "Your post just hit 1,000 likes. Screenshot it!", "Milestone unlocked", "trophy"),
    ("Buzz", "New poll: pineapple on pizza? 10K votes so far", "Cast your vote", "trending"),
]


# ---------------------------------------------------------------------------
# IMAGES SHOWN WHEN A NOTIFICATION IS CLICKED
# Small vector illustrations on a 100 x 70 grid, drawn with canvas shapes.
# Shapes: ("r", x0,y0,x1,y1, colour)  ("o", cx,cy,rx,ry, colour)  ("p", [x,y,...], colour)
#         ("l", [x,y,...], colour, width)  ("t", x,y, text, colour, size)
# ---------------------------------------------------------------------------
EMAIL_ICONS = {   # which image goes with the notification that teases each email
    "Dana Whitfield": "clock", "IT Security": "lock", "Dr. Patel's Office": "calendar",
    "Marcus Lee (Client)": "document", "Finance Department": "document",
    "Hollis Property Management": "house", "Priya Nair": "calendar", "Sprint Bot": "chart",
    "Sam Ortiz": "document", "Conference Committee": "bird", "Mom": "plate",
    "City Library": "books", "Streamline Weekly": "bulb", "ShopMart": "box",
    "FitLife Gym": "dumbbell", "Maple Street Neighbors": "balloons", "DealDrop": "tag",
}
for _e in EMAILS:
    _e["icon"] = EMAIL_ICONS[_e["sender"]]

ILLUSTRATIONS = {
    # ---- images that illustrate specific emails
    "clock": ("#fdf0d5", [("o", 28, 12, 7, 7, "#e63946"), ("o", 72, 12, 7, 7, "#e63946"),
        ("l", [32, 60, 26, 68], "#555", 2), ("l", [68, 60, 74, 68], "#555", 2),
        ("o", 50, 36, 28, 28, "#c62828"), ("o", 50, 36, 24, 24, "#ffffff"),
        ("l", [50, 36, 50, 18], "#222", 2.5), ("l", [50, 36, 64, 42], "#222", 2.5),
        ("o", 50, 36, 2.5, 2.5, "#222")]),
    "lock": ("#e3f0ff", [("o", 50, 26, 16, 18, "#44546a"), ("o", 50, 28, 10, 12, "#e3f0ff"),
        ("r", 30, 34, 70, 64, "#f2b705"), ("o", 50, 46, 5, 5, "#3b3128"), ("r", 48, 48, 52, 57, "#3b3128")]),
    "calendar": ("#eaf7ee", [("r", 22, 12, 78, 62, "#ffffff"), ("r", 22, 12, 78, 26, "#e5484d"),
        ("r", 32, 7, 36, 17, "#555"), ("r", 64, 7, 68, 17, "#555"),
        *[("r", x, y, x + 9, y + 6, "#d9dee7") for x in (29, 43, 57) for y in (32, 42, 52)],
        ("r", 43, 42, 52, 48, "#e5484d")]),
    "document": ("#f5f0ff", [("r", 30, 8, 70, 64, "#ffffff"), ("p", [58, 8, 70, 8, 70, 20], "#d0d5dd"),
        ("r", 36, 14, 54, 18, "#3a6ea5"), *[("r", 36, y, 64, y + 2, "#9aa4b2") for y in (26, 33, 40, 47)],
        ("l", [38, 57, 44, 53, 50, 58, 58, 52], "#c62828", 1.5)]),
    "house": ("#e8f4fa", [("r", 0, 62, 100, 70, "#6cbf6c"), ("r", 28, 34, 72, 62, "#f4d9a6"),
        ("p", [20, 34, 50, 10, 80, 34], "#c0392b"), ("r", 45, 44, 57, 62, "#8b5a2b"),
        ("r", 32, 40, 42, 50, "#8ec5ff"), ("r", 60, 40, 70, 50, "#8ec5ff")]),
    "chart": ("#fff7e6", [("l", [20, 10, 20, 60, 85, 60], "#555", 1.5),
        *[("r", 28 + i * 14, 60 - h, 38 + i * 14, 60, c) for i, (h, c) in enumerate(
            ((18, "#3a6ea5"), (28, "#30a46c"), (22, "#f5a524"), (40, "#8e4ec6")))],
        ("l", [33, 38, 47, 28, 61, 34, 75, 16], "#e5484d", 1.5)]),
    "bird": ("#e6f5ff", [("o", 15, 14, 8, 8, "#ffd166"), ("r", 30, 58, 80, 62, "#8b5a2b"),
        ("p", [34, 38, 22, 30, 24, 42], "#2b4f7a"), ("o", 48, 38, 16, 12, "#3a6ea5"),
        ("o", 46, 40, 9, 6, "#2b4f7a"), ("o", 64, 30, 8, 8, "#3a6ea5"), ("p", [71, 29, 80, 32, 71, 34], "#f5a524"),
        ("o", 66, 28, 1.6, 1.6, "#ffffff"), ("l", [46, 50, 46, 58], "#f5a524", 1.5), ("l", [53, 50, 53, 58], "#f5a524", 1.5)]),
    "plate": ("#fff0e0", [("r", 0, 50, 100, 70, "#c9a27a"), ("o", 50, 40, 30, 14, "#ffffff"),
        ("o", 50, 39, 22, 10, "#efefef"), ("o", 50, 38, 14, 6, "#d9534f"), ("o", 50, 36, 12, 4, "#f4c542"),
        ("l", [14, 28, 14, 52], "#888", 1.5), ("l", [86, 28, 86, 52], "#888", 1.5)]),
    "books": ("#eef5e8", [("r", 10, 58, 90, 63, "#8b5a2b"), ("r", 24, 46, 76, 58, "#3a6ea5"),
        ("r", 28, 34, 72, 46, "#e5484d"), ("r", 22, 22, 70, 34, "#f5a524"), ("r", 26, 10, 66, 22, "#30a46c"),
        *[("r", x0, y, x1, y + 2, "#ffffff") for x0, x1, y in ((24, 76, 50), (28, 72, 38), (22, 70, 26), (26, 66, 14))]]),
    "bulb": ("#fff9d6", [("o", 50, 28, 18, 18, "#ffd54a"), ("r", 42, 42, 58, 50, "#ffd54a"),
        ("r", 42, 50, 58, 54, "#9aa4b2"), ("r", 44, 54, 56, 58, "#7b8494"),
        ("l", [46, 30, 50, 38, 54, 30], "#c77d00", 1.2),
        *[("l", [50 + math.cos(math.radians(d)) * 24, 28 + math.sin(math.radians(d)) * 24,
                 50 + math.cos(math.radians(d)) * 32, 28 + math.sin(math.radians(d)) * 32], "#f5a524", 2)
          for d in (-160, -130, -100, -80, -50, -20)]]),
    "box": ("#f3eadf", [("p", [24, 26, 50, 36, 50, 62, 24, 52], "#c08a4f"), ("p", [76, 26, 50, 36, 50, 62, 76, 52], "#a9733c"),
        ("p", [24, 26, 50, 16, 76, 26, 50, 36], "#d9a566"), ("l", [37, 21, 63, 31], "#f5e6c8", 3)]),
    "dumbbell": ("#ffe8e8", [("r", 0, 58, 100, 70, "#d8c3a5"), ("r", 28, 33, 72, 37, "#555"),
        ("r", 20, 22, 28, 48, "#333"), ("r", 14, 27, 20, 43, "#555"), ("r", 72, 22, 80, 48, "#333"), ("r", 80, 27, 86, 43, "#555")]),
    "balloons": ("#e8f6ff", [("r", 0, 62, 100, 70, "#7fc97f"),
        ("l", [32, 39, 50, 62], "#666", 0.6), ("l", [50, 33, 50, 62], "#666", 0.6), ("l", [68, 39, 50, 62], "#666", 0.6),
        ("o", 32, 24, 12, 15, "#e5484d"), ("o", 50, 18, 12, 15, "#f5a524"), ("o", 68, 24, 12, 15, "#8e4ec6")]),
    "tag": ("#ffeaf0", [("p", [22, 36, 40, 18, 74, 18, 74, 54, 40, 54], "#e63946"), ("o", 36, 36, 3.5, 3.5, "#ffeaf0"),
        ("t", 59, 36, "20%", "#ffffff", 9)]),
    # ---- images for the social-media notifications
    "likes": ("#ffe8ef", [("o", 42, 28, 14, 14, "#ed4956"), ("o", 58, 28, 14, 14, "#ed4956"),
        ("p", [29, 35, 71, 35, 50, 62], "#ed4956"),
        ("o", 20, 18, 3.5, 3.5, "#ff8fa3"), ("o", 26, 18, 3.5, 3.5, "#ff8fa3"), ("p", [17, 20, 29, 20, 23, 28], "#ff8fa3"),
        ("o", 78, 12, 3, 3, "#ff8fa3"), ("o", 84, 12, 3, 3, "#ff8fa3"), ("p", [75, 14, 87, 14, 81, 22], "#ff8fa3")]),
    "follower": ("#e8f0ff", [("o", 44, 26, 10, 10, "#8a96a8"), ("o", 44, 54, 20, 16, "#8a96a8"),
        ("o", 68, 22, 11, 11, "#0095f6"), ("r", 67, 16, 69, 28, "#ffffff"), ("r", 62, 21, 74, 23, "#ffffff")]),
    "comment": ("#eef7ee", [("o", 38, 26, 22, 14, "#ffffff"), ("p", [24, 34, 20, 46, 34, 38], "#ffffff"),
        ("o", 30, 26, 2.5, 2.5, "#8a96a8"), ("o", 38, 26, 2.5, 2.5, "#8a96a8"), ("o", 46, 26, 2.5, 2.5, "#8a96a8"),
        ("o", 64, 46, 20, 11, "#0095f6"), ("p", [76, 52, 84, 62, 68, 54], "#0095f6"),
        ("r", 52, 43, 74, 45, "#ffffff"), ("r", 52, 48, 68, 50, "#ffffff")]),
    "clip": ("#1a1a2e", [("r", 32, 3, 68, 67, "#3a3a4f"), ("r", 34, 5, 66, 65, "#2b2d42"),
        ("p", [45, 26, 45, 40, 57, 33], "#ffffff"), ("r", 37, 54, 55, 56, "#ffffff"), ("r", 37, 59, 49, 61, "#9aa4b2"),
        ("o", 74, 26, 3, 3, "#fe2c55"), ("o", 79, 26, 3, 3, "#fe2c55"), ("p", [71, 27.5, 82, 27.5, 76.5, 34], "#fe2c55"),
        ("o", 76, 44, 4.5, 4.5, "#ffffff"), ("o", 76, 58, 4.5, 4.5, "#25f4ee")]),
    "live": ("#fce4ec", [("o", 50, 33, 26, 26, "#e1306c"), ("o", 50, 33, 23, 23, "#fce4ec"), ("o", 50, 33, 20, 20, "#8a96a8"),
        ("o", 50, 27, 7, 7, "#e9ecf2"), ("o", 50, 44, 12, 7, "#e9ecf2"),
        ("r", 36, 54, 64, 66, "#e1306c"), ("t", 50, 60, "LIVE", "#ffffff", 7)]),
    "trending": ("#fff3e0", [("p", [44, 6, 60, 30, 56, 52, 44, 62, 32, 52, 28, 30], "#ff6b35"),
        ("p", [44, 26, 52, 40, 49, 54, 44, 58, 39, 54, 36, 40], "#ffd166"),
        ("p", [74, 40, 82, 28, 90, 40], "#30a46c"), ("r", 80, 40, 84, 56, "#30a46c")]),
    "story": ("#fde6f0", [("o", 50, 35, 26, 26, "#f58529"), ("o", 50, 35, 23, 23, "#dd2a7b"), ("o", 50, 35, 20, 20, "#fde6f0"),
        ("o", 50, 35, 17, 17, "#8ec5ff"), ("o", 44, 30, 4, 4, "#ffd166"), ("o", 50, 47, 12, 5, "#6cbf6c")]),
    "photo": ("#e9eef5", [("r", 22, 6, 78, 64, "#ffffff"), ("r", 26, 10, 74, 44, "#9bd1ff"), ("o", 36, 20, 5, 5, "#ffd166"),
        ("p", [26, 44, 44, 24, 60, 44], "#5c7a99"), ("p", [46, 44, 62, 28, 74, 44], "#3f5b78"),
        ("r", 26, 49, 58, 51, "#9aa4b2"), ("r", 26, 54, 46, 56, "#c5ccd6"),
        ("o", 64.5, 56, 2.4, 2.4, "#ed4956"), ("o", 69, 56, 2.4, 2.4, "#ed4956"), ("p", [62.3, 57, 71.2, 57, 66.7, 62], "#ed4956")]),
    "dm": ("#e6f4ff", [("p", [20, 36, 82, 14, 46, 40], "#0095f6"), ("p", [46, 40, 82, 14, 60, 58], "#0077c8"),
        ("p", [46, 40, 52, 54, 60, 58], "#005fa3")]),
    "views": ("#ebf5ff", [("o", 50, 26, 32, 18, "#3a6ea5"), ("o", 50, 26, 30, 16, "#ffffff"), ("o", 50, 26, 11, 11, "#3a6ea5"),
        ("o", 50, 26, 5, 5, "#111111"), ("o", 46, 22, 2, 2, "#ffffff"),
        ("r", 30, 52, 36, 64, "#30a46c"), ("r", 40, 48, 46, 64, "#30a46c"), ("r", 50, 44, 56, 64, "#30a46c"),
        ("r", 60, 38, 66, 64, "#30a46c")]),
    "trophy": ("#fff8e1", [("o", 33, 19, 6, 7, "#f5b400"), ("o", 33, 19, 3, 4, "#fff8e1"), ("o", 67, 19, 6, 7, "#f5b400"),
        ("o", 67, 19, 3, 4, "#fff8e1"), ("p", [36, 8, 64, 8, 60, 34, 40, 34], "#f5b400"), ("r", 47, 34, 53, 46, "#d99a00"),
        ("r", 38, 46, 62, 54, "#8b5a2b"), ("r", 34, 54, 66, 59, "#6b4423"),
        ("p", [50, 13, 52, 19, 58, 19, 53, 23, 55, 29, 50, 25, 45, 29, 47, 23, 42, 19, 48, 19], "#fff3b0")]),
    "mention": ("#efeaff", [("t", 50, 35, "@", "#5b5bd6", 40), ("o", 72, 14, 7, 7, "#ed4956"), ("t", 72, 14, "1", "#ffffff", 7)]),
    "sound": ("#ebebff", [("o", 36, 50, 9, 7, "#5b5bd6"), ("o", 62, 44, 9, 7, "#5b5bd6"), ("r", 43, 16, 46, 50, "#5b5bd6"),
        ("r", 69, 10, 72, 44, "#5b5bd6"), ("p", [43, 16, 72, 10, 72, 18, 43, 24], "#5b5bd6")]),
    "mail": ("#e6f0ff", [("r", 22, 18, 78, 54, "#ffffff"), ("p", [22, 18, 78, 18, 50, 40], "#d6e4ff"),
        ("l", [22, 54, 42, 34], "#b6c8ee", 1.2), ("l", [78, 54, 58, 34], "#b6c8ee", 1.2),
        ("l", [22, 18, 50, 40, 78, 18], "#7a9ad6", 1.5)]),
}


def draw_illustration(c, key, w, h):
    """Draw the named illustration onto canvas c (w x h pixels)."""
    bg, items = ILLUSTRATIONS.get(key, ILLUSTRATIONS["mail"])
    c.delete("all")
    c.configure(bg=bg)
    sx, sy = w / 100, h / 70
    pts = lambda v: [x * (sx if i % 2 == 0 else sy) for i, x in enumerate(v)]
    for it in items:
        k = it[0]
        if k == "r":
            c.create_rectangle(it[1] * sx, it[2] * sy, it[3] * sx, it[4] * sy, fill=it[5], outline="")
        elif k == "o":
            cx, cy, rx, ry = it[1:5]
            c.create_oval((cx - rx) * sx, (cy - ry) * sy, (cx + rx) * sx, (cy + ry) * sy, fill=it[5], outline="")
        elif k == "p":
            c.create_polygon(pts(it[1]), fill=it[2], outline="")
        elif k == "l":
            c.create_line(pts(it[1]), fill=it[2], width=it[3] * sx, capstyle="round", joinstyle="round")
        elif k == "t":
            c.create_text(it[1] * sx, it[2] * sy, text=it[3], fill=it[4], font=("Helvetica", int(it[5] * sx), "bold"))


class EmailApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inbox")
        self.geometry("1250x700")
        self.minsize(800, 450)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.last_title = None
        self.current = None
        self.toast_visible = False
        self._hide_job = None
        self.popup = None
        self.score = 0
        self.replies = {}          # email index -> the reply that was sent
        self.drafts = {}           # email index -> unsent draft text
        self.reply_times = {}      # email index -> time the reply was sent
        self.cur_idx = None        # email currently open
        self._build_mail_panel()
        self._build_toast()

        for seq in ("<Control-plus>", "<Control-equal>", "<Control-KP_Add>"):
            self.bind(seq, lambda e: self._zoom(+0.1))
        for seq in ("<Control-minus>", "<Control-KP_Subtract>"):
            self.bind(seq, lambda e: self._zoom(-0.1))
        self.bind("<Control-0>", lambda e: self._zoom(None))

        self.after(NOTIFICATION_GAP_MS, self._show_notification)   # first one after the pause

    # ------------------------------------------------------------ left: inbox
    def _build_mail_panel(self, select="0"):
        outer = tk.Frame(self, bg="#ffffff")
        self.mail_frame = outer
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        header = tk.Frame(outer, bg="#1a73e8")
        self.header = header
        header.grid(row=0, column=0, sticky="ew")
        tk.Label(header, text="Inbox", bg="#1a73e8", fg="white", padx=16, pady=8,
                 font=F("Helvetica", 16, "bold")).pack(side="left")
        self.score_label = tk.Label(header, bg="#0b57c2", fg="#ffffff", padx=14, pady=4,
                                    font=F("Helvetica", 13, "bold"))
        self.score_label.pack(side="right", padx=12)
        tk.Label(header, text="sorted by importance", bg="#1a73e8", fg="#d6e6ff", padx=8,
                 font=F("Helvetica", 10)).pack(side="right")

        paned = ttk.PanedWindow(outer, orient="horizontal")
        paned.grid(row=1, column=0, sticky="nsew")

        # --- email list
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Mail.Treeview", font=F("Helvetica", 10), rowheight=int(28 * FONT_SCALE),
                        background="#ffffff", fieldbackground="#ffffff", foreground="#222222", borderwidth=0)
        style.configure("Mail.Treeview.Heading", font=F("Helvetica", 10, "bold"),
                        background="#e4e7ec", foreground="#222222")
        style.map("Mail.Treeview", background=[("selected", "#1a73e8")],
                  foreground=[("selected", "#ffffff")])

        list_frame = tk.Frame(paned)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        tree = ttk.Treeview(list_frame, style="Mail.Treeview", show="headings", selectmode="browse",
                            columns=("level", "sender", "subject", "time", "status"))
        for col, title, width in (("level", "Importance", 105), ("sender", "From", 125),
                                  ("subject", "Subject", 190), ("time", "Received", 78),
                                  ("status", "Status", 92)):
            tree.heading(col, text=title, anchor="w")
            tree.column(col, width=int(width * FONT_SCALE), minwidth=int(60 * FONT_SCALE), anchor="w",
                        stretch=(col == "subject"))
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        for minimum, name, colour, tint in LEVELS:
            tree.tag_configure(name, background=tint, foreground="#222222")
        for i, e in enumerate(EMAILS):
            name = level_of(e["score"])[0]
            tree.insert("", "end", iid=str(i), tags=(name,),
                        values=(f"{name}  ({e['score']})", e["sender"], e["subject"], e["time"],
                                self._status_text(i)))
        tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree = tree

        # --- reading pane + reply box
        read_frame = tk.Frame(paned, bg="#ffffff")
        read_frame.rowconfigure(0, weight=1)
        read_frame.columnconfigure(0, weight=1)
        reader = tk.Text(read_frame, wrap="word", bg="#ffffff", fg="#222222", relief="flat",
                         padx=24, pady=16, font=F("Helvetica", 12), spacing3=6,
                         borderwidth=0, highlightthickness=0, cursor="arrow",
                         selectbackground="#b3d4ff", selectforeground="#000000")
        rsb = ttk.Scrollbar(read_frame, orient="vertical", command=reader.yview)
        reader.configure(yscrollcommand=rsb.set)
        reader.grid(row=0, column=0, sticky="nsew")
        rsb.grid(row=0, column=1, sticky="ns")
        reader.tag_configure("subject", font=F("Helvetica", 17, "bold"), spacing3=10)
        reader.tag_configure("meta", font=F("Helvetica", 10), foreground="#666666", spacing3=2)
        reader.tag_configure("rule", font=F("Helvetica", 4), spacing3=8)
        reader.tag_configure("body", font=F("Helvetica", 12), spacing2=3)
        for _, name, colour, _tint in LEVELS:
            reader.tag_configure("badge_" + name, font=F("Helvetica", 10, "bold"),
                                 foreground="#ffffff", background=colour)
        reader.tag_configure("thread_note", font=F("Helvetica", 9, "bold"), foreground="#1a73e8", spacing3=6)
        reader.tag_configure("msg_head", font=F("Helvetica", 11, "bold"), spacing3=1)
        reader.tag_configure("divider", font=F("Helvetica", 4), background="#d5dae3", spacing3=10)
        reader.tag_configure("reply_block", background="#eaf3ff", lmargin1=10, lmargin2=10, rmargin=10)
        reader.tag_configure("badge_you", font=F("Helvetica", 10, "bold"), foreground="#ffffff",
                             background="#1e7e34")
        self.reader = reader

        PANEL = "#f4f6fa"
        reply = tk.Frame(read_frame, bg=PANEL, highlightthickness=1, highlightbackground="#d5dae3")
        reply.grid(row=1, column=0, columnspan=2, sticky="ew")
        reply.columnconfigure(0, weight=1)
        tk.Label(reply, text="Reply", bg=PANEL, fg="#222222", anchor="w",
                 font=F("Helvetica", 11, "bold")).grid(row=0, column=0, sticky="w", padx=14, pady=(8, 2))
        self.points_hint = tk.Label(reply, bg=PANEL, fg="#555555", font=F("Helvetica", 10, "bold"))
        self.points_hint.grid(row=0, column=1, sticky="e", padx=14, pady=(8, 2))
        self.reply_box = tk.Text(reply, height=3, wrap="word", font=F("Helvetica", 11), bg="#ffffff",
                                 fg="#222222", insertbackground="#222222",
                                 selectbackground="#b3d4ff", selectforeground="#000000",
                                 relief="solid", borderwidth=1, padx=8, pady=6, undo=True)
        self.reply_box.grid(row=1, column=0, columnspan=2, sticky="ew", padx=14)
        self.reply_box.bind("<Control-Return>", lambda e: (self._send_reply(), "break")[1])
        bar = tk.Frame(reply, bg=PANEL)
        bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=8)
        self.send_btn = tk.Button(bar, text="Send reply", command=self._send_reply, relief="flat",
                                  bg="#1a73e8", fg="#ffffff", activebackground="#1558b0",
                                  activeforeground="#ffffff", padx=14, pady=4,
                                  font=F("Helvetica", 11, "bold"))
        self.send_btn.pack(side="left")
        self.reply_status = tk.Label(bar, bg=PANEL, fg="#555555", font=F("Helvetica", 10), anchor="w")
        self.reply_status.pack(side="left", padx=12)

        paned.add(read_frame, weight=2)      # the open email (left)
        paned.add(list_frame, weight=3)      # the inbox list (right)

        def set_split():            # the open email gets ~40%, the inbox list ~60%
            try:
                paned.sashpos(0, int(paned.winfo_width() * 0.40))
            except tk.TclError:
                pass
        self.after(60, set_split)

        self._update_score()
        tree.selection_set(select)
        tree.focus(select)

    # ---- scoring helpers
    def _points_for(self, i):
        return POINTS[level_of(EMAILS[i]["score"])[0]]

    def _status_text(self, i):
        return "Replied \u2713" if i in self.replies else f"{self._points_for(i)} pts"

    def _update_score(self):
        best = sum(self._points_for(i) for i in range(len(EMAILS)))
        self.score_label.configure(
            text=f"Score: {self.score} / {best}    Replied: {len(self.replies)}/{len(EMAILS)}")

    def _save_draft(self):
        """Remember unsent text when switching emails."""
        i = self.cur_idx
        if i is not None and i not in self.replies:
            self.drafts[i] = self.reply_box.get("1.0", "end-1c")

    # ---- reading + replying
    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        self._save_draft()
        i = self.cur_idx = int(sel[0])
        e = EMAILS[i]
        self._render_email(i)
        self.reader.yview_moveto(0)
        self._load_reply_state(i)

    def _render_email(self, i):
        """Show the email; if it has been answered, show the reply beneath it as a thread."""
        e = EMAILS[i]
        name, _, _ = level_of(e["score"])
        replied = i in self.replies
        r = self.reader
        r.configure(state="normal")
        r.delete("1.0", "end")
        r.insert("end", e["subject"] + "\n", "subject")
        if replied:
            r.insert("end", "CONVERSATION  -  2 messages\n", "thread_note")
        # message 1: the original email
        r.insert("end", f"{e['sender']}  <{e['address']}>\n", "msg_head")
        r.insert("end", "To: you@example.com\n", "meta")
        r.insert("end", f"Received: {e['time']}\n", "meta")
        r.insert("end", "Importance: ", "meta")
        r.insert("end", f" {name.upper()} - {e['score']}/100 ", "badge_" + name)
        r.insert("end", "\n\n", "rule")
        r.insert("end", e["body"] + "\n", "body")
        # message 2: your reply
        if replied:
            r.insert("end", "\n", "divider")
            block = ("reply_block",)
            r.insert("end", " YOU REPLIED ", ("badge_you",))
            r.insert("end", "\n", block)
            r.insert("end", "You  <you@example.com>\n", ("msg_head",) + block)
            r.insert("end", f"To: {e['sender']}\n", ("meta",) + block)
            r.insert("end", f"Sent: {self.reply_times[i]}\n", ("meta",) + block)
            r.insert("end", "Re: " + e["subject"] + "\n", ("meta",) + block)
            r.insert("end", "\n", ("rule",) + block)
            r.insert("end", self.replies[i] + "\n", ("body",) + block)
        r.configure(state="disabled")

    def _load_reply_state(self, i):
        box = self.reply_box
        box.configure(state="normal")
        box.delete("1.0", "end")
        if i in self.replies:                                   # already answered
            box.insert("1.0", "Your reply is shown in the conversation above.")
            box.configure(state="disabled", bg="#eef1f5", fg="#777777")
            self.send_btn.configure(state="disabled", text="Sent")
            self.points_hint.configure(text="")
            self.reply_status.configure(text=f"Replied - earned {self._points_for(i)} points", fg="#1e7e34")
        else:
            box.insert("1.0", self.drafts.get(i, ""))
            box.configure(bg="#ffffff", fg="#222222")
            self.send_btn.configure(state="normal", text="Send reply")
            self.points_hint.configure(text=f"Worth {self._points_for(i)} points")
            self.reply_status.configure(text="Ctrl+Enter also sends", fg="#777777")

    def _send_reply(self):
        i = self.cur_idx
        if i is None or i in self.replies:
            return
        text = self.reply_box.get("1.0", "end-1c").strip()
        if len(text) < MIN_REPLY_CHARS:
            self.reply_status.configure(text=f"Write at least {MIN_REPLY_CHARS} characters to reply.",
                                        fg="#c62828")
            return
        pts = self._points_for(i)
        self.replies[i] = text
        self.reply_times[i] = datetime.now().strftime("%I:%M %p").lstrip("0")
        self.drafts.pop(i, None)
        self.score += pts
        self.tree.set(str(i), "status", self._status_text(i))
        self._update_score()
        self._render_email(i)
        self.reader.see("end")                     # scroll down to the new reply
        self._load_reply_state(i)
        self.reply_status.configure(text=f"Reply sent!  +{pts} points", fg="#1e7e34")
        if len(self.replies) == len(EMAILS):
            messagebox.showinfo("Inbox cleared", f"You answered every email!\nFinal score: {self.score}")

    # ------------------------------------- top-right phone notification
    CARD = "#262c36"

    def _build_toast(self):
        w = int(330 * FONT_SCALE)
        icon = int(26 * FONT_SCALE)
        t = tk.Frame(self, bg=self.CARD, highlightthickness=1, highlightbackground="#3f4856")
        tk.Frame(t, width=w, height=1, bg=self.CARD).pack()            # sets the card width

        top = tk.Frame(t, bg=self.CARD)
        top.pack(fill="x", padx=14, pady=(10, 0))
        self.t_icon = tk.Canvas(top, width=icon, height=icon, bg=self.CARD, highlightthickness=0)
        self.t_icon.pack(side="left")
        self.t_oval = self.t_icon.create_oval(1, 1, icon - 1, icon - 1, outline="")
        self.t_letter = self.t_icon.create_text(icon / 2, icon / 2, fill="white",
                                                font=F("Helvetica", 11, "bold"))
        self.t_app = tk.Label(top, bg=self.CARD, fg="#aeb4c0", font=F("Helvetica", 9, "bold"))
        self.t_app.pack(side="left", padx=8)
        tk.Label(top, text="now", bg=self.CARD, fg="#7f8796",
                 font=F("Helvetica", 9)).pack(side="right")

        self.t_title = tk.Label(t, bg=self.CARD, fg="#ffffff", justify="left", anchor="w",
                                wraplength=w - 28, font=F("Helvetica", 13, "bold"))
        self.t_title.pack(fill="x", padx=14, pady=(8, 0))
        self.t_sub = tk.Label(t, bg=self.CARD, fg="#b8bfcc", justify="left", anchor="w",
                              wraplength=w - 28, font=F("Helvetica", 11))
        self.t_sub.pack(fill="x", padx=14, pady=(2, 12))
        self.toast = t                                                   # not placed yet = hidden
        self._make_clickable(t)

    def _make_clickable(self, widget):
        widget.configure(cursor="hand2")
        widget.bind("<Button-1>", self._on_toast_click)
        for child in widget.winfo_children():
            self._make_clickable(child)

    def _on_toast_click(self, _event=None):
        """Open the image for the notification, and dismiss the card early."""
        if not self.current:
            return
        self._show_image_popup(self.current)
        if self._hide_job is not None:                   # card fully shown: close it now
            self.after_cancel(self._hide_job)
            self._hide_job = None
            self._hide_notification()

    def _show_image_popup(self, notif):
        if notif[0] in ("Gramly", "Clipt"):
            self._show_photo_popup(notif)
        else:
            self._show_static_popup(notif)

    def _show_static_popup(self, notif):
        app, title, sub, icon = notif
        if self.popup is not None and self.popup.winfo_exists():
            self.popup.destroy()
        p = self.popup = tk.Toplevel(self)
        p.title(app)
        p.configure(bg="#0f1419")
        p.transient(self)
        p.resizable(False, False)
        w, h = 440, 308
        canvas = tk.Canvas(p, width=w, height=h, highlightthickness=0)
        canvas.pack(padx=16, pady=(16, 10))
        draw_illustration(canvas, icon, w, h)
        tk.Label(p, text=app.upper(), bg="#0f1419", fg=APP_COLORS[app],
                 font=F("Helvetica", 9, "bold")).pack(anchor="w", padx=18)
        tk.Label(p, text=title, bg="#0f1419", fg="#ffffff", wraplength=w, justify="left",
                 font=F("Helvetica", 14, "bold")).pack(anchor="w", padx=18)
        tk.Label(p, text=sub, bg="#0f1419", fg="#b8bfcc", wraplength=w, justify="left",
                 font=F("Helvetica", 11)).pack(anchor="w", padx=18, pady=(2, 10))
        tk.Button(p, text="Close", command=p.destroy, padx=16).pack(pady=(0, 14))
        p.bind("<Escape>", lambda e: p.destroy())
        p.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - p.winfo_reqwidth()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - p.winfo_reqheight()) // 2
        p.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _show_photo_popup(self, notif):
        """Instagram-style static photo post, using local PNGs when present."""
        app, title, subtitle, icon = notif
        if self.popup is not None and self.popup.winfo_exists():
            self.popup.destroy()
        p = self.popup = tk.Toplevel(self)
        p.title("Instagram-style photo post")
        p.configure(bg="white")
        p.geometry("430x690")
        p.resizable(False, False)
        p.transient(self)

        handle = "maya.creates" if app == "Gramly" else "dance.with.dee"
        for name in ("graham_smith", "mike.makes", "priya.travels", "jordan_runs"):
            if name.split("_")[0].split(".")[0] in title.lower():
                handle = name
                break

        header = tk.Frame(p, bg="white", pady=10)
        header.pack(fill="x")
        avatar = tk.Canvas(header, width=36, height=36, bg="white", highlightthickness=0)
        avatar.pack(side="left", padx=(14, 9))
        avatar.create_oval(2, 2, 34, 34, fill="#e1306c", outline="#ffba57", width=2)
        avatar.create_text(18, 18, text=handle[0].upper(), fill="white", font=F("Helvetica", 12, "bold"))
        tk.Label(header, text=handle, bg="white", fg="#171717",
                 font=F("Helvetica", 11, "bold")).pack(side="left")
        tk.Button(header, text="✕", bg="white", fg="#333333", relief="flat",
                  command=p.destroy, font=F("Helvetica", 13)).pack(side="right", padx=12)

        photo = tk.Canvas(p, width=410, height=410, bg="#f0f0f0", highlightthickness=0)
        photo.pack(fill="x", padx=10)
        folder = "instagram" if app == "Gramly" else "tiktok"

        # Pick a random local Instagram image each time a Gramly notification is clicked.
        # Tkinter PhotoImage reliably supports PNG/GIF/PPM/PGM without extra libraries.
        if app == "Gramly":
            image_dir = PHOTOS_DIR / "instagram"
            supported = {".png", ".gif", ".ppm", ".pgm"}
            image_files = [
                path for path in image_dir.iterdir()
                if path.is_file() and path.suffix.lower() in supported
            ] if image_dir.is_dir() else []
            image_path = random.choice(image_files) if image_files else None
        else:
            image_dir = PHOTOS_DIR / "tiktok"
            image_path = image_dir / "mock-tiktok.png"

        image = None
        if image_path is not None and image_path.is_file():
            try:
                image = tk.PhotoImage(file=str(image_path))
                factor = max(1, math.ceil(image.width() / 410),
                             math.ceil(image.height() / 410))
                if factor > 1:
                    image = image.subsample(factor, factor)
            except tk.TclError as exc:
                print(f"Could not load {image_path}: {exc}")
        if image is not None:
            photo.image = image  # Keep Tkinter's image reference alive.
            photo.create_image(205, 205, image=image)
        else:
            draw_illustration(photo, icon, 410, 410)
            hint = ("Add PNG/GIF images to media/instagram/" if app == "Gramly"
                    else "Add a photo: media/tiktok/mock-tiktok.png")
            photo.create_text(205, 385, text=hint,
                              fill="#222222", font=F("Helvetica", 10, "bold"))

        state = {"liked": False, "saved": False, "following": False}
        actions = tk.Frame(p, bg="white")
        actions.pack(fill="x", padx=13, pady=(7, 0))
        likes_label = tk.Label(p, text="1,284 likes", bg="white", fg="#111111",
                               font=F("Helvetica", 10, "bold"), anchor="w")
        like_button = tk.Button(actions, text="♡", font=F("Helvetica", 23),
                                bg="white", relief="flat", fg="#111111")
        like_button.pack(side="left")

        def toggle_like():
            state["liked"] = not state["liked"]
            like_button.config(text="♥" if state["liked"] else "♡",
                               fg="#e1306c" if state["liked"] else "#111111")
            likes_label.config(text=f"{1284 + int(state['liked']):,} likes")

        like_button.config(command=toggle_like)

        def comments():
            messagebox.showinfo("Comments", "sam.eats: Love this! ❤️\n"
                                "jordan_runs: This is amazing 🔥\n"
                                "maya.codes: Where is this?", parent=p)

        tk.Button(actions, text="▢", command=comments, font=F("Helvetica", 20),
                  bg="white", relief="flat").pack(side="left", padx=5)
        tk.Button(actions, text="➤", font=F("Helvetica", 18), bg="white", relief="flat",
                  command=lambda: messagebox.showinfo("Share", "Sharing is simulated.", parent=p)
                  ).pack(side="left", padx=4)
        save_button = tk.Button(actions, text="♧", font=F("Helvetica", 20),
                                bg="white", relief="flat")
        save_button.pack(side="right")

        def toggle_save():
            state["saved"] = not state["saved"]
            save_button.config(text="▣" if state["saved"] else "♧")

        save_button.config(command=toggle_save)
        likes_label.pack(fill="x", padx=17, pady=(2, 3))
        tk.Label(p, text=f"{handle}  {title}", bg="white", fg="#111111",
                 font=F("Helvetica", 10), wraplength=390,
                 justify="left", anchor="w").pack(fill="x", padx=17)
        tk.Label(p, text=subtitle, bg="white", fg="#777777",
                 font=F("Helvetica", 9), anchor="w").pack(fill="x", padx=17, pady=(3, 0))
        follow = tk.Button(p, text="Follow", bg="#0095f6", fg="white", relief="flat",
                           font=F("Helvetica", 10, "bold"))
        follow.pack(anchor="w", padx=17, pady=8)

        def toggle_follow():
            state["following"] = not state["following"]
            follow.config(text="Following" if state["following"] else "Follow",
                          bg="#eeeeee" if state["following"] else "#0095f6",
                          fg="#222222" if state["following"] else "white")

        follow.config(command=toggle_follow)
        p.bind("<Escape>", lambda _e: p.destroy())

    def _pick_notification(self):
        """~10% relate to an email's content; the rest are ordinary social-media notifications."""
        for _ in range(10):
            if random.random() < RELATED_CHANCE:
                e = random.choice(EMAILS)
                notif = (random.choice(list(APP_COLORS)), e["notif"],
                         f"New message from {e['sender']}", e["icon"])
            else:
                notif = random.choice(GENERIC_NOTIFS)
            if notif[1] != self.last_title:
                break
        self.last_title = notif[1]
        return notif

    def _fill_toast(self, notif):
        app, title, sub, _icon = notif
        self.t_icon.itemconfig(self.t_oval, fill=APP_COLORS[app])
        self.t_icon.itemconfig(self.t_letter, text=app[0])
        self.t_app.configure(text=app.upper())
        self.t_title.configure(text=title)
        self.t_sub.configure(text=sub)

    def _place_toast(self, y):
        self.toast.place(relx=1.0, rely=0.0, anchor="ne", x=-18, y=y)
        self.toast.lift()

    def _toast_y(self):
        """Resting position: just below the blue header bar, so the score stays visible."""
        return self.header.winfo_reqheight() + 12

    def _slide(self, start, end, done=None, step=0, steps=10):
        """Slide the card vertically (from above the window down into the top-right corner)."""
        t = step / steps
        self._place_toast(int(start + (end - start) * (1 - (1 - t) ** 2)))   # ease-out
        if step < steps:
            self.after(15, self._slide, start, end, done, step + 1, steps)
        elif done:
            done()

    def _offscreen_y(self):
        self.toast.update_idletasks()
        return -(self.toast.winfo_reqheight() + 40)          # just above the top edge

    def _show_notification(self):
        self.current = self._pick_notification()
        self._fill_toast(self.current)
        self.toast_visible = True
        self._slide(self._offscreen_y(), self._toast_y(), done=self._schedule_hide)

    def _schedule_hide(self):
        self._hide_job = self.after(NOTIFICATION_SHOW_MS, self._auto_hide)

    def _auto_hide(self):
        self._hide_job = None
        self._hide_notification()

    def _hide_notification(self):
        self._slide(self._toast_y(), self._offscreen_y(), done=self._finish_hide)

    def _finish_hide(self):
        self.toast.place_forget()
        self.toast_visible = False
        self.after(NOTIFICATION_GAP_MS, self._show_notification)

    # ------------------------------------------------------------------ zoom
    def _zoom(self, delta=None):
        global FONT_SCALE
        FONT_SCALE = DEFAULT_SCALE if delta is None else min(3.0, max(0.7, round(FONT_SCALE + delta, 2)))
        sel = self.tree.selection()
        self._save_draft()
        self.cur_idx = None                      # so the rebuilt (empty) box doesn't overwrite the draft
        self.mail_frame.destroy()
        self._build_mail_panel(sel[0] if sel else "0")
        self.toast.destroy()
        self._build_toast()
        if self.toast_visible and self.current:          # keep a visible notification on screen
            self._fill_toast(self.current)
            self._place_toast(self._toast_y())
        self.title(f"Inbox  (text size {int(FONT_SCALE * 100)}%)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inbox + phone notifications")
    parser.add_argument("--scale", type=float, default=FONT_SCALE,
                        help="text size multiplier, e.g. 1.5 (default %(default)s)")
    args = parser.parse_args()
    FONT_SCALE = DEFAULT_SCALE = args.scale
    EmailApp().mainloop()
"""
SAT Reading Practice + YouTube player

Install:   pip install PyQt6 PyQt6-WebEngine
Run:       python sat_app.py

- Main window: SAT-style multiple-choice READING practice (passage questions and
  vocabulary in context) at three difficulty levels.
- A small YouTube player is embedded in the bottom-right corner of the main window.
  Paste any YouTube link (video, youtu.be, shorts, or playlist) and press Play.
- The video follows the difficulty of the question on screen:
    Easy          -> video plays normally
    Intermediate  -> picture hidden, audio keeps playing at a lower volume
    Hard          -> video paused completely
- Hard questions never appear in the first half of a session.
- File > Load questions (JSON)... lets you add your own questions.
  Format: a list of objects like
    {"section": "Reading Comprehension", "level": "easy", "passage": "(optional)", "prompt": "...",
     "choices": ["a", "b", "c", "d"], "answer": 0, "explanation": "..."}
  where "answer" is the 0-based index of the correct choice, and "level" is
  "easy", "intermediate" or "hard" (optional, defaults to "intermediate").
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
    # ======================= EASY (very simple) =======================
    {"section": "Vocabulary in Context", "level": "easy",
     "prompt": "Which word means the same as 'big'?",
     "choices": ["large", "small", "red", "fast"], "answer": 0,
     "explanation": "'Big' and 'large' both mean great in size."},
    {"section": "Vocabulary in Context", "level": "easy",
     "prompt": "Which word means the opposite of 'hot'?",
     "choices": ["cold", "warm", "sunny", "dry"], "answer": 0,
     "explanation": "'Cold' is the opposite of 'hot'."},
    {"section": "Vocabulary in Context", "level": "easy",
     "prompt": "Which word best completes the sentence?\n\nThe dog wagged its ______ when it saw its owner.",
     "choices": ["tail", "wing", "fin", "horn"], "answer": 0,
     "explanation": "Dogs wag their tails when they are happy."},
    {"section": "Vocabulary in Context", "level": "easy",
     "prompt": "Which word means the same as 'happy'?",
     "choices": ["glad", "angry", "tired", "hungry"], "answer": 0,
     "explanation": "'Glad' means feeling pleased or happy."},
    {"section": "Reading Comprehension", "level": "easy",
     "passage": "Sam has a red ball. He kicks it across the yard.",
     "prompt": "What color is Sam's ball?",
     "choices": ["red", "blue", "green", "yellow"], "answer": 0,
     "explanation": "The text says Sam has a red ball."},
    {"section": "Reading Comprehension", "level": "easy",
     "passage": "Lila woke up early on Saturday. She put on her boots and went outside to feed the chickens.",
     "prompt": "What did Lila do after she put on her boots?",
     "choices": ["She went back to bed.", "She went outside to feed the chickens.",
                 "She ate breakfast.", "She rode her bike."], "answer": 1,
     "explanation": "The text says she put on her boots and went outside to feed the chickens."},
    {"section": "Reading Comprehension", "level": "easy",
     "passage": "Penguins are birds that cannot fly. They use their wings to swim.",
     "prompt": "What do penguins use their wings for?",
     "choices": ["flying", "swimming", "digging", "climbing"], "answer": 1,
     "explanation": "The text says penguins use their wings to swim."},
    {"section": "Reading Comprehension", "level": "easy",
     "passage": "It was a cold winter day. Tom wore his hat, gloves, and a warm coat.",
     "prompt": "Why did Tom wear a warm coat?",
     "choices": ["Because it was hot", "Because it was cold",
                 "Because he was going swimming", "Because it was his birthday"], "answer": 1,
     "explanation": "The text says it was a cold winter day."},

    # ================= INTERMEDIATE (simple, a little more reading) =================
    {"section": "Vocabulary in Context", "level": "intermediate",
     "prompt": "Which word is closest in meaning to 'enormous'?",
     "choices": ["tiny", "huge", "quiet", "quick"], "answer": 1,
     "explanation": "'Enormous' means very large, which is 'huge'."},
    {"section": "Vocabulary in Context", "level": "intermediate",
     "prompt": "Which word means the opposite of 'ancient'?",
     "choices": ["modern", "old", "broken", "large"], "answer": 0,
     "explanation": "'Ancient' means very old, so the opposite is 'modern'."},
    {"section": "Vocabulary in Context", "level": "intermediate",
     "prompt": "Which word best completes the sentence?\n\nAfter the long hike, the travelers were so ______ "
               "that they fell asleep as soon as they sat down.",
     "choices": ["exhausted", "delighted", "curious", "generous"], "answer": 0,
     "explanation": "Falling asleep right away after a long hike points to being very tired: 'exhausted'."},
    {"section": "Reading Comprehension", "level": "intermediate",
     "passage": "Bees collect nectar from flowers to make honey. While they do this, pollen sticks to their "
                "bodies and is carried to other flowers, which helps plants make seeds.",
     "prompt": "According to the text, how do bees help plants?",
     "choices": ["By eating their leaves", "By carrying pollen from flower to flower",
                 "By digging up the soil", "By blocking the sunlight"], "answer": 1,
     "explanation": "The text says pollen sticks to bees and is carried to other flowers, helping plants make seeds."},
    {"section": "Reading Comprehension", "level": "intermediate",
     "passage": "Maya packed her lunch, grabbed her umbrella, and checked the sky one more time. Gray clouds "
                "covered the hills, and the wind had started to pick up. She decided to leave early so she "
                "wouldn't be caught in the storm.",
     "prompt": "Based on the text, why did Maya decide to leave early?",
     "choices": ["She was late for lunch.", "She was worried about an approaching storm.",
                 "She had forgotten her umbrella.", "She wanted to enjoy the sunshine."], "answer": 1,
     "explanation": "The gray clouds and rising wind suggest a storm, and the text says she left early to avoid it."},
    {"section": "Reading Comprehension", "level": "intermediate",
     "passage": "The library on Pine Street opens at 9 a.m. on weekdays and 10 a.m. on weekends. It closes at "
                "6 p.m. every day except Friday, when it stays open until 8 p.m. for evening study sessions.",
     "prompt": "According to the text, what time does the library close on Friday?",
     "choices": ["6 p.m.", "8 p.m.", "9 a.m.", "10 a.m."], "answer": 1,
     "explanation": "The text says it stays open until 8 p.m. on Friday."},

    {"section": "Reading Comprehension", "level": "intermediate",
     "passage": "A caterpillar eats leaves all day to grow bigger. After a few weeks, it wraps itself in a "
                "cocoon. Inside, it slowly changes into a butterfly.",
     "prompt": "What happens right after the caterpillar wraps itself in a cocoon?",
     "choices": ["It eats more leaves.", "It slowly changes inside the cocoon.",
                 "It flies away right away.", "It digs underground."], "answer": 1,
     "explanation": "The text says that inside the cocoon, the caterpillar slowly changes into a butterfly."},
    {"section": "Vocabulary in Context", "level": "intermediate",
     "prompt": "Which word best completes the sentence?\n\nThe baby was ______, so she smiled and laughed all afternoon.",
     "choices": ["cheerful", "gloomy", "furious", "sleepy"], "answer": 0,
     "explanation": "Smiling and laughing show a happy mood: 'cheerful'."},
    {"section": "Reading Comprehension", "level": "intermediate",
     "passage": "When Ana got home, the kitchen floor was wet, her dog was covered in mud, and the back door "
                "was open.",
     "prompt": "What most likely happened?",
     "choices": ["Ana went swimming.", "The dog went outside, got muddy, and came back in.",
                 "Someone cleaned the floor.", "It was a hot, sunny day."], "answer": 1,
     "explanation": "A muddy dog, a wet floor and an open back door suggest the dog went out and came back in."},
    {"section": "Reading Comprehension", "level": "intermediate",
     "passage": "Recycling helps the planet. When we recycle paper, glass, and cans, we make less trash. We "
                "also save energy, because new items do not have to be made from scratch.",
     "prompt": "What is the main idea of the passage?",
     "choices": ["Recycling is expensive.", "Recycling helps the planet by making less trash and saving energy.",
                 "Paper is the most common kind of trash.", "Everyone should buy new things."], "answer": 1,
     "explanation": "The whole passage explains how recycling helps: less trash and less energy used."},

    # (more hard questions)
    {"section": "Vocabulary in Context", "level": "hard",
     "prompt": "Which choice completes the text with the most logical and precise word?\n\n"
               "The scientist's explanation was ______; even readers with no background in physics could follow it.",
     "choices": ["lucid", "ornate", "tentative", "elusive"], "answer": 0,
     "explanation": "The clause after the semicolon says anyone could follow it, so the explanation was clear: 'lucid'."},
    {"section": "Vocabulary in Context", "level": "hard",
     "prompt": "Which choice completes the text with the most logical and precise word?\n\n"
               "Although the new policy was meant to help, many residents found its rules so ______ that they "
               "could not tell what was actually required of them.",
     "choices": ["ambiguous", "ambitious", "affordable", "enthusiastic"], "answer": 0,
     "explanation": "Residents couldn't tell what was required, so the rules were unclear: 'ambiguous'."},
    {"section": "Vocabulary in Context", "level": "hard",
     "passage": "The coach's feedback was blunt but never cruel: she told players exactly what needed to change "
                "and then showed them how to fix it.",
     "prompt": "As used in the text, what does 'blunt' most nearly mean?",
     "choices": ["straightforward", "dull", "angry", "careless"], "answer": 0,
     "explanation": "The text says she told players exactly what to change, so 'blunt' means direct and "
                    "straightforward here, not 'dull' (the other common meaning)."},
    {"section": "Reading Comprehension", "level": "hard",
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
    {"section": "Reading Comprehension", "level": "hard",
     "passage": "Octopuses are known for their talent at escaping. One aquarium noticed that fish were "
                "disappearing overnight. Staff eventually discovered that the octopus was leaving its tank, "
                "eating fish from a neighboring tank, and returning to its own tank before morning.",
     "prompt": "Which inference is best supported by the text?",
     "choices": ["The octopus was not being fed enough.",
                 "The octopus could move between tanks without being noticed.",
                 "The aquarium staff had been feeding the fish too little.",
                 "Octopuses prefer to live in groups."], "answer": 1,
     "explanation": "The octopus left, ate, and came back before morning without being caught, so it could move "
                    "between tanks unnoticed. The text says nothing about feeding or group living."},
    {"section": "Reading Comprehension", "level": "hard",
     "passage": "For decades, many people believed the Great Wall of China could be seen from space with the "
                "naked eye. In reality, astronauts have reported that the wall is far too narrow to pick out "
                "from orbit. Highways and city lights are much easier to spot.",
     "prompt": "Which choice best describes the main purpose of the text?",
     "choices": ["To correct a common misconception", "To argue that the wall should be preserved",
                 "To describe how the wall was built", "To compare ancient and modern structures"], "answer": 0,
     "explanation": "The text states a popular belief and then explains why it is not true."},

    # ========================= HARD =========================
    {"section": "Vocabulary in Context", "level": "hard",
     "prompt": "Which choice completes the text with the most logical and precise word?\n\n"
               "The senator's reply was characteristically ______: although it sounded like a direct answer, "
               "it committed her to nothing.",
     "choices": ["evasive", "candid", "exuberant", "meticulous"], "answer": 0,
     "explanation": "A reply that sounds direct but commits to nothing is avoiding the question: 'evasive'. "
                    "'Candid' would mean frank and open, the opposite."},
    {"section": "Reading Comprehension", "level": "hard",
     "passage": "Economists often assume that people choose the cheapest option available. But a study of "
                "grocery shoppers found that many consistently paid more for a familiar brand, even when an "
                "identical store brand sat on the same shelf. The researchers concluded that the shoppers "
                "were not being irrational; they were paying for the certainty that the product would taste "
                "the way they expected.",
     "prompt": "Which choice best describes the researchers' conclusion?",
     "choices": ["Shoppers are generally careless with their money.",
                 "Paying more can reflect a reasonable preference for predictability.",
                 "Store brands are lower in quality than name brands.",
                 "Economists' assumptions hold true for all shoppers."], "answer": 1,
     "explanation": "The researchers say shoppers 'were not being irrational' but were paying for certainty. "
                    "Choice B restates this. The text never says store brands are worse."},
    {"section": "Reading Comprehension", "level": "hard",
     "passage": "Critics of the restoration argued that repainting the mural would erase decades of weathering "
                "that had become part of its character. Yet the conservators pointed out that the 'weathering' "
                "admirers loved was largely soot and grime obscuring the artist's original colors. Cleaning, "
                "not repainting, they said, would reveal the artwork rather than replace it.",
     "prompt": "How do the conservators respond to the critics' concern?",
     "choices": ["By arguing that the weathering the critics value is actually dirt covering the original colors",
                 "By agreeing that repainting would erase the mural's character",
                 "By proposing to replace the mural with an exact copy",
                 "By claiming that the artist intended the mural to age"], "answer": 0,
     "explanation": "The conservators say the 'weathering' is mostly soot and grime hiding the original colors, "
                    "and that cleaning would reveal the work."},
    {"section": "Reading Comprehension", "level": "hard",
     "passage": "Although the novel was widely praised on release for its sweeping plot, later readers have "
                "tended to admire something quieter: the way the narrator's descriptions of ordinary rooms and "
                "meals reveal her loneliness without her ever naming it.",
     "prompt": "What does the text suggest about later readers' view of the novel?",
     "choices": ["They find the plot more impressive than early readers did.",
                 "They value its subtle portrayal of the narrator's emotions more than its plot.",
                 "They believe the narrator names her loneliness too often.",
                 "They think the novel was overpraised on release."], "answer": 1,
     "explanation": "Later readers admire 'something quieter': the indirect way loneliness is shown. "
                    "The text doesn't say they dislike the plot or think the novel was overpraised."},
    {"section": "Reading Comprehension", "level": "hard",
     "prompt": "A student claims that rooftop gardens can lower a building's energy use. Which finding, if "
               "true, would most directly support the student's claim?",
     "choices": ["Rooftop gardens are popular with residents.",
                 "Buildings with rooftop gardens had summer cooling costs 15% lower than similar buildings without them.",
                 "Rooftop gardens require regular watering.",
                 "Many rooftop gardens grow herbs and vegetables."], "answer": 1,
     "explanation": "Only choice B connects rooftop gardens to a measurable drop in energy use (cooling costs)."},
    {"section": "Reading Comprehension", "level": "hard",
     "passage": "Researchers studying sleep found that students who slept eight hours before an exam scored "
                "higher on average than students who stayed up studying. However, the students who slept more "
                "had also tended to begin studying earlier in the week.",
     "prompt": "Which choice most logically completes the text? \"This suggests that ______\"",
     "choices": ["all-night studying is always harmful.",
                 "the score difference may be due partly to when students began studying, not to sleep alone.",
                 "sleeping eight hours is unnecessary before an exam.",
                 "studying earlier in the week has no effect on scores."], "answer": 1,
     "explanation": "The sleepers also started studying earlier, so that could explain some of the difference. "
                    "The other choices overreach beyond the evidence."},
]

# --------------------------------------------------------------------------
# Lots more VERY EASY questions (kept compact: built from the tables below)
# --------------------------------------------------------------------------
def _mc(section, prompt, right, wrong, explanation, passage=None, level="easy"):
    """Build a question whose first choice is the right one (answer order is shuffled at runtime)."""
    q = {"section": section, "level": level, "prompt": prompt,
         "choices": [right] + list(wrong), "answer": 0, "explanation": explanation}
    if passage:
        q["passage"] = passage
    return q


# (word, same meaning, three wrong answers)
_SYNONYMS = [
    ("small", "tiny", ["giant", "loud", "green"]),
    ("fast", "quick", ["slow", "heavy", "sleepy"]),
    ("begin", "start", ["stop", "finish", "wait"]),
    ("sad", "unhappy", ["joyful", "silly", "brave"]),
    ("smart", "clever", ["lazy", "quiet", "messy"]),
    ("shut", "close", ["open", "break", "lift"]),
    ("jump", "leap", ["crawl", "sit", "sleep"]),
    ("pretty", "beautiful", ["ugly", "noisy", "heavy"]),
    ("afraid", "scared", ["brave", "sleepy", "hungry"]),
    ("rock", "stone", ["feather", "cloud", "puddle"]),
]

# (word, opposite, three wrong answers)
_OPPOSITES = [
    ("up", "down", ["high", "over", "top"]),
    ("day", "night", ["morning", "noon", "sunny"]),
    ("full", "empty", ["heavy", "round", "tall"]),
    ("open", "closed", ["wide", "empty", "loud"]),
    ("tall", "short", ["thin", "wide", "long"]),
    ("soft", "hard", ["quiet", "warm", "smooth"]),
    ("wet", "dry", ["cold", "muddy", "clean"]),
    ("early", "late", ["first", "soon", "quick"]),
]

# (sentence, right word, three wrong words)
_FILL_INS = [
    ("I wear a ______ on my head when it is cold.", "hat", ["shoe", "sock", "spoon"]),
    ("A bird can ______ in the sky.", "fly", ["dig", "drive", "melt"]),
    ("We use ______ to cut paper.", "scissors", ["a spoon", "a pillow", "a ladder"]),
    ("The sun rises in the ______.", "morning", ["night", "moon", "snow"]),
    ("Fish live in the ______.", "water", ["tree", "desert", "cloud"]),
    ("I brush my ______ every morning.", "teeth", ["socks", "desk", "window"]),
    ("A cow gives us ______.", "milk", ["eggs", "wool", "honey"]),
    ("We read a ______ to enjoy a story.", "book", ["fork", "door", "shoe"]),
]

# (passage, question, right answer, three wrong answers, explanation)
_EASY_PASSAGES = [
    ("Mia has a small brown dog named Biscuit. Every afternoon, they walk to the park.",
     "What is the dog's name?", "Biscuit", ["Mia", "Brownie", "Max"],
     "The text says the dog is named Biscuit."),
    ("The bus comes at 7:30 each morning. Jake waits at the corner with his backpack.",
     "What does Jake have with him?", "A backpack", ["An umbrella", "A kite", "A skateboard"],
     "The text says he waits with his backpack."),
    ("A snail moves very slowly. It carries its shell on its back.",
     "Where does a snail carry its shell?", "On its back", ["In its mouth", "On its head", "In a bag"],
     "The text says it carries its shell on its back."),
    ("Grandma baked a chocolate cake for Ben's birthday. Ben blew out the candles and made a wish.",
     "What kind of cake did Grandma bake?", "Chocolate", ["Vanilla", "Strawberry", "Lemon"],
     "The text says she baked a chocolate cake."),
    ("Ants work together to carry food back to their nest. Many ants can lift a crumb that one ant "
     "cannot move.",
     "Why do ants work together?", "To move food that is too big for one ant",
     ["To play a game", "To scare other animals", "To keep warm"],
     "Many ants can lift a crumb that one ant cannot move."),
    ("On Monday, Zoe planted a seed in a pot. By Friday, a tiny green sprout had popped up.",
     "What happened by Friday?", "A tiny green sprout grew", ["The pot broke", "Zoe bought a new pot", "It snowed"],
     "The text says a tiny green sprout had popped up."),
    ("Max put on his swim trunks and grabbed a towel. He jumped into the pool with a big splash.",
     "Where did Max jump?", "Into the pool", ["Into the ocean", "Onto the couch", "Into a boat"],
     "The text says he jumped into the pool."),
    ("The moon is bright at night. Stars twinkle in the dark sky.",
     "When is the moon bright, according to the text?", "At night", ["At lunch", "At breakfast", "At recess"],
     "The text says the moon is bright at night."),
    ("Kai's bike has two wheels, a bell, and a basket.",
     "How many wheels does Kai's bike have?", "Two", ["One", "Three", "Four"],
     "The text says the bike has two wheels."),
    ("Rosa wrote a letter to her friend. She put a stamp on the envelope and dropped it in the mailbox.",
     "Where did Rosa put the letter?", "In the mailbox", ["In her backpack", "In the trash", "Under her bed"],
     "She dropped it in the mailbox."),
    ("Frogs start life as eggs in the water. The eggs hatch into tadpoles, which grow legs and become frogs.",
     "What do frog eggs hatch into?", "Tadpoles", ["Fish", "Birds", "Snails"],
     "The text says the eggs hatch into tadpoles."),
    ("The class went to the zoo on Tuesday. They saw lions, monkeys, and a giant tortoise.",
     "Which animal did the class see?", "A monkey", ["A whale", "A horse", "A penguin"],
     "The text lists monkeys among the animals they saw."),
    ("Eli was thirsty after soccer practice. He drank a big glass of water.",
     "Why did Eli drink water?", "He was thirsty", ["He was cold", "He was sleepy", "He was lost"],
     "The text says Eli was thirsty."),
    ("It rained all morning, so the picnic was moved inside. The family ate sandwiches on the living room floor.",
     "Why was the picnic moved inside?", "Because of the rain",
     ["Because the park was closed", "Because they were late", "Because it was too hot"],
     "The text says it rained all morning."),
    ("Honeybees live in a hive. They make honey from flower nectar.",
     "What do honeybees make honey from?", "Nectar from flowers", ["Tree bark", "Rain water", "Grass seeds"],
     "The text says they make honey from flower nectar."),
    ("Nina has three pencils, two erasers, and one ruler in her pencil case.",
     "How many pencils does Nina have?", "Three", ["One", "Two", "Four"],
     "The text says she has three pencils."),
    ("Dad turned on the oven and put the pizza inside. After twenty minutes, the whole house smelled delicious.",
     "What did Dad put in the oven?", "A pizza", ["A cake", "A pie", "Bread"],
     "The text says he put the pizza inside."),
    ("The tree in Lucas's yard drops its leaves in the fall. In winter, the branches are bare.",
     "When are the tree's branches bare?", "In winter", ["In summer", "In spring", "On his birthday"],
     "The text says the branches are bare in winter."),
    ("Tara loves to draw. She uses crayons to make pictures of animals.",
     "What does Tara use to draw?", "Crayons", ["Chalk", "Paint", "Markers"],
     "The text says she uses crayons."),
    ("A giraffe has a very long neck. It uses it to reach leaves at the tops of tall trees.",
     "Why does a giraffe use its long neck?", "To reach leaves high in the trees",
     ["To swim", "To dig holes", "To hide from the rain"],
     "The text says it uses its neck to reach leaves at the tops of tall trees."),
    ("Owen's alarm rang at 6:00. He got out of bed, brushed his teeth, and ate breakfast.",
     "What did Owen do right after getting out of bed?", "He brushed his teeth",
     ["He ate breakfast", "He went to school", "He watched TV"],
     "He got out of bed, then brushed his teeth, then ate breakfast."),
    ("The farmer wakes up early to milk the cows. Then he feeds the chickens and collects eggs.",
     "What does the farmer do right after milking the cows?", "He feeds the chickens",
     ["He goes back to bed", "He plants corn", "He drives to town"],
     "The text says 'Then he feeds the chickens.'"),
    ("Sara found a shiny shell on the beach. She put it in her pocket to take home.",
     "Where did Sara find the shell?", "On the beach", ["In her garden", "In a store", "At school"],
     "The text says she found it on the beach."),
    ("Whales are not fish. They are mammals that breathe air through a hole on top of their heads.",
     "How do whales breathe?", "Through a hole on top of their heads",
     ["Through gills", "Through their tails", "Through their fins"],
     "The text says they breathe air through a hole on top of their heads."),
    ("Ravi was nervous about his first day at a new school. But his teacher smiled and showed him his "
     "desk, and soon he felt better.",
     "How did Ravi feel at the start of the day?", "Nervous", ["Bored", "Silly", "Proud"],
     "The text says he was nervous about his first day."),
    ("In the fall, geese fly south, where it is warmer. They fly in a V shape.",
     "Why do geese fly south in the fall?", "To find warmer weather",
     ["To find snow", "To visit the zoo", "To learn to swim"],
     "The text says they fly south where it is warmer."),
]

for _w, _right, _wrong in _SYNONYMS:
    QUESTIONS.append(_mc("Vocabulary in Context", f"Which word means the same as '{_w}'?", _right, _wrong,
                         f"'{_w.capitalize()}' and '{_right}' mean almost the same thing."))
for _w, _right, _wrong in _OPPOSITES:
    QUESTIONS.append(_mc("Vocabulary in Context", f"Which word means the opposite of '{_w}'?", _right, _wrong,
                         f"'{_right.capitalize()}' is the opposite of '{_w}'."))
for _sentence, _right, _wrong in _FILL_INS:
    QUESTIONS.append(_mc("Vocabulary in Context",
                         "Which word best completes the sentence?\n\n" + _sentence, _right, _wrong,
                         f"'{_right}' is the choice that makes the sentence make sense."))
for _passage, _question, _right, _wrong, _why in _EASY_PASSAGES:
    QUESTIONS.append(_mc("Reading Comprehension", _question, _right, _wrong, _why, passage=_passage))

LETTERS = "ABCD"

# Question difficulty -> what the video does
VIDEO_MODE = {"easy": "video", "intermediate": "audio", "hard": "pause"}
VOLUME = {"video": 100, "audio": 30, "pause": 100}   # % volume per mode (audio = intermediate questions)
SPEED = {"video": 1, "audio": 1, "pause": 1}          # playback speed per mode (YouTube allows 0.25-2)
MODE_LABEL = {"video": "▶ Video on", "audio": f"🎧 Audio only · {VOLUME['audio']}% volume",
              "pause": "⏸ Paused"}

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


PLAYER_HTML = """PLAYER_HTML =
<html>
<body style="margin:0;background:#000">

<iframe id="yt"
    src="__SRC__"
    style="position:absolute;inset:0;width:100%;height:100%;border:0"
    allow="autoplay; encrypted-media; picture-in-picture"
    referrerpolicy="strict-origin-when-cross-origin">
</iframe>

<div id="cover" style="
    position:absolute;
    inset:0;
    display:flex;
    align-items:center;
    justify-content:center;
    background:#e9ecf5;
    color:#000;
    font:600 16px sans-serif;
    text-align:center;
    padding:16px;
    opacity:0;
    visibility:hidden;
    transition:opacity 1.5s ease;
    pointer-events:none;">
</div>

<script>

var VOL = __VOL__;
var RATE = __RATE__;
var cur = "__MODE__";

// Transition settings
const FADE_DURATION = 3000;  // milliseconds
const FADE_STEPS = 30;

let currentVolume = VOL[cur];
let fadeInterval = null;
let pauseTimeout = null;

function cmd(f, a) {
    document.getElementById("yt").contentWindow.postMessage(
        JSON.stringify({
            event:"command",
            func:f,
            args:a===undefined ? "" : a
        }),
        "*"
    );
}

function setVolume(v) {
    currentVolume = Math.max(0, Math.min(100, v));
    cmd("setVolume", [Math.round(currentVolume)]);
}

function rate(m) {
    cmd("setPlaybackRate", [RATE[m]]);
}

// Gradually change volume
function fadeVolume(target, duration, callback) {

    if (fadeInterval !== null) {
        clearInterval(fadeInterval);
        fadeInterval = null;
    }

    let startVolume = currentVolume;
    let startTime = performance.now();

    fadeInterval = setInterval(function() {

        let elapsed = performance.now() - startTime;
        let progress = Math.min(elapsed / duration, 1);

        // Smooth easing
        let eased = progress * progress * (3 - 2 * progress);

        let newVolume =
            startVolume + (target - startVolume) * eased;

        setVolume(newVolume);

        if (progress >= 1) {

            clearInterval(fadeInterval);
            fadeInterval = null;

            setVolume(target);

            if (callback) callback();
        }

    }, duration / FADE_STEPS);
}

// Gradually show/hide video
function fadeVideo(show, message) {

    let cover = document.getElementById("cover");

    if (message) {
        cover.textContent = message;
    }

    if (show) {
        cover.style.opacity = "0";

        setTimeout(function() {
            if (cover.style.opacity === "0") {
                cover.style.visibility = "hidden";
            }
        }, FADE_DURATION);

    } else {
        cover.style.visibility = "visible";
        cover.style.opacity = "1";
    }
}

// Main transition function
function setMode(m) {

    if (pauseTimeout !== null) {
        clearTimeout(pauseTimeout);
        pauseTimeout = null;
    }

    cur = m;

    cmd("unMute");
    rate(m);

    if (m === "video") {

        // Resume playback
        cmd("playVideo");

        // Gradually reveal video
        fadeVideo(true);

        // Fade audio to full volume
        fadeVolume(VOL.video, FADE_DURATION);

    } else if (m === "audio") {

        // Keep video playing
        cmd("playVideo");

        // Gradually hide picture
        fadeVideo(false, "🎧 Audio only");

        // Reduce volume gradually
        fadeVolume(VOL.audio, FADE_DURATION);

    } else if (m === "pause") {

        // Gradually hide picture
        fadeVideo(false, "⏸ Paused during hard questions");

        // Fade audio to silence
        fadeVolume(0, FADE_DURATION, function() {

            // Only pause if still in hard mode
            if (cur === "pause") {
                cmd("pauseVideo");
            }
        });
    }
}

// Initial appearance
function initializePlayer() {

    if (cur === "video") {

        fadeVideo(true);
        setVolume(VOL.video);

    } else if (cur === "audio") {

        fadeVideo(false, "🎧 Audio only");
        setVolume(VOL.audio);

    } else {

        fadeVideo(false, "⏸ Paused during hard questions");
        setVolume(0);
        cmd("pauseVideo");
    }
}

// Reapply settings while YouTube initializes
function applySettingsSoon() {

    [500, 1500, 3000, 6000].forEach(function(t) {

        setTimeout(function() {

            if (fadeInterval === null) {
                setVolume(cur === "pause" ? 0 : VOL[cur]);
            }

            rate(cur);

        }, t);
    });
}

document.getElementById("yt").addEventListener(
    "load",
    applySettingsSoon
);

initializePlayer();
applySettingsSoon();

</script>
</body>
</html>
"""


class VideoPanel(QWidget):
    """Small YouTube player embedded in the main window (bottom-right)."""

    def __init__(self):
        super().__init__()
        self.setObjectName("videoPanel")
        self.setFixedSize(640, 480)
        self.mode = "video"   # "video" | "audio" | "pause"
        self.status = QLabel(MODE_LABEL[self.mode])
        self.curVol = 100
        self.fadeTimer = 0

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
        header = QHBoxLayout()
        header.addWidget(QLabel("YouTube player"))
        header.addStretch(1)
        header.addWidget(self.status)
        layout.addLayout(header)
        layout.addLayout(bar)
        layout.addWidget(self.view, 1)

    def play(self):
        src = youtube_embed_url(self.url_input.text())
        if not src:
            self.show_message("That doesn't look like a YouTube link.")
            return
        # Start in whatever state the current question calls for.
        autoplay = 0 if self.mode == "pause" else 1
        src = src.replace("autoplay=1", f"autoplay={autoplay}")
        src += "&enablejsapi=1&origin=https%3A%2F%2Flocalhost"
        html = PLAYER_HTML.replace("__SRC__", src).replace("__MODE__", self.mode).replace("__VOL__", json.dumps(VOLUME)).replace("__RATE__", json.dumps(SPEED))
        # A real-looking base URL gives YouTube the origin/referrer it wants for embeds.
        self.view.setHtml(html, QUrl("https://localhost/"))

    def set_mode(self, mode):
        """Switch between normal video, audio-only and paused (only acts on a change)."""
        if mode == self.mode:
            return
        self.mode = mode
        self.status.setText(MODE_LABEL[mode])
        self.view.page().runJavaScript(f'if (typeof setMode === "function") setMode("{mode}");')

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

        self.setWindowTitle("SAT Reading Practice")
        self.resize(1100, 740)
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
        self.level_box = QComboBox()
        self.level_box.addItems(["All", "Easy", "Intermediate", "Hard"])
        self.level_box.currentIndexChanged.connect(self.start_session)
        self.meta = QLabel(objectName="meta")
        self.video_btn = QPushButton("Show / hide video")
        self.video_btn.clicked.connect(self.toggle_video)
        top.addWidget(QLabel("Section:"))
        top.addWidget(self.section_box)
        top.addWidget(QLabel("Difficulty:"))
        top.addWidget(self.level_box)
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
        v.addLayout(bottom)

        # centers the video player horizontally
        video_row = QHBoxLayout()
        video_row.addStretch(1)
        video_row.addWidget(self.video)
        video_row.addStretch(1)

        v.addLayout(video_row)

        v.addStretch(1)

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
        lvl = self.level_box.currentText().lower()
        qs = [dict(q) for q in self.all_questions
              if sec in ("All", q["section"]) and lvl in ("all", q.get("level", "intermediate"))]
        random.shuffle(qs)
        # Hard questions are held back until the second half of the session.
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
        self.show_question()

    def show_question(self):
        if not self.pool:
            self.prompt.setText("No questions in this section.")
            return
        q = self.pool[self.i]
        self.video.set_mode(VIDEO_MODE[q.get("level", "intermediate")])
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
        level = self.pool[self.i].get("level", "intermediate").title()
        self.meta.setText(f"Question {self.i + 1} of {len(self.pool)}   |   Level: {level}   |   "
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
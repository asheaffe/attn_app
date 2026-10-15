"""
Dog Article Viewer
------------------
Left 80%:  a scrollable, academic-style article about dogs
           (with a table, four figures, and a reference list).
Right 20%: an endlessly scrolling group chat about mundane things
           (about 10% of messages mention dogs).
           Some messages include photos. Put your own images in the
           folders inside PHOTOS_DIR (see below); otherwise small built-in
           illustrations are drawn. Or run:  python dog_app.py --photos <folder>

Uses only the Python standard library (tkinter). Run with:  python dog_app.py
"""

import math
import random
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import argparse

try:                                  # Pillow is optional; it adds JPG/WebP/BMP support + smoother resizing
    from PIL import Image, ImageOps, ImageTk
except ImportError:
    Image = ImageOps = ImageTk = None

# ---------------------------------------------------------------------------
# TEXT SIZE.  Change FONT_SCALE to make ALL text bigger or smaller
# (1.0 = original size, 1.3 = 30% bigger, 1.6 = 60% bigger, ...).
# While the app is running you can also press Ctrl + / Ctrl - / Ctrl 0.
# You can also start it with:  python dog_app.py --scale 1.5
# ---------------------------------------------------------------------------
FONT_SCALE = 1.3
DEFAULT_SCALE = FONT_SCALE


def F(family, size, *style):
    """Build a tkinter font tuple with the current FONT_SCALE applied."""
    return (family, max(1, round(size * FONT_SCALE)), *style)


# ---------------------------------------------------------------------------
# ARTICLE CONTENT.  Block types: title, subtitle, abstract, keywords, h1, p,
# fig (name, caption), table (caption), ref.  Edit freely.
# ---------------------------------------------------------------------------
ARTICLE = [
    ("title", "The Domestic Dog (Canis lupus familiaris): Origins, Biology, Cognition, "
              "and Human-Animal Relationships"),
    ("subtitle", "A Narrative Review"),
    ("abstract",
     "The domestic dog is the oldest domesticated animal and the most morphologically diverse "
     "terrestrial mammal. This review synthesizes current evidence on the origins of dogs, the "
     "genetic basis of their physical variation, their sensory biology, their social cognition, "
     "and their health and roles in human society. Genomic and archaeological data indicate that "
     "the dog lineage diverged from wolves at least 20,000 years ago, although the timing and "
     "geography of domestication remain contested. Dogs differ from wolves in sensory capacities, "
     "in their sensitivity to human social cues, and in a suite of correlated traits often called "
     "the domestication syndrome. Studying dogs illuminates general questions about evolution, "
     "cognition, and cross-species cooperation, with practical implications for animal welfare "
     "and public health."),
    ("keywords", "domestication; canine genomics; olfaction; social cognition; human-animal interaction"),

    ("h1", "1. Introduction"),
    ("p", "Dogs have lived alongside humans for longer than any other domesticated species, and they "
          "occupy an unusually wide range of ecological and social niches, from working partners and "
          "household companions to free-ranging scavengers. Widely cited estimates place the global dog "
          "population at several hundred million to roughly one billion animals, the majority of them "
          "free-ranging (Hughes & Macdonald, 2013). Dogs are also a powerful scientific model: their "
          "shared environment with humans, extensive veterinary records, and well-defined breed "
          "structure make them useful for studying genetics, aging, and behaviour. This review "
          "summarizes what is known about canine origins (Section 2), genetics and morphology "
          "(Section 3), sensory biology (Section 4), cognition (Section 5), health (Section 6), and "
          "roles in society (Section 7)."),

    ("h1", "2. Origins and Domestication"),
    ("p", "Genomic evidence indicates that dogs descend from an extinct population of Late Pleistocene "
          "wolves rather than from any living wolf population. Estimates for the divergence of the dog "
          "and wolf lineages span roughly 20,000 to more than 40,000 years ago, depending on the "
          "mutation rate and calibration assumptions used (Bergström et al., 2020; Frantz et al., "
          "2016). Among the oldest widely accepted dog remains is a burial at Bonn-Oberkassel, "
          "Germany, dated to about 14,200 years ago, while several older specimens remain disputed "
          "(Figure 1)."),
    ("fig", "timeline",
     "Figure 1. Selected milestones in the history of the domestic dog on a logarithmic time axis. "
     "The shaded bar shows the range of published estimates for the dog-wolf divergence; dates for "
     "later events are approximate."),
    ("p", "Whether domestication occurred once or more than once is still debated. Frantz et al. (2016) "
          "proposed a dual origin in separate Eurasian populations, whereas later analyses of ancient "
          "genomes found that a single origin from a structured wolf population is also consistent "
          "with the data (Bergström et al., 2020)."),
    ("p", "Diet was probably an important selective pressure. Axelsson et al. (2013) reported that dogs "
          "carry more copies of the pancreatic amylase gene AMY2B than wolves, along with variants in "
          "other starch-digestion genes, consistent with adaptation to human-associated, starch-rich "
          "diets. A separate line of evidence comes from the farm-fox experiment begun by Dmitri "
          "Belyaev in 1959, in which selecting silver foxes solely for tameness produced, within a few "
          "generations, animals with floppy ears, altered coat colours, and other traits typical of "
          "domesticated animals (Trut, 1999). These correlated changes are collectively termed the "
          "domestication syndrome and have been attributed to subtle effects on neural crest cells "
          "during development (Wilkins et al., 2014)."),

    ("h1", "3. Genetics and Morphological Diversity"),
    ("p", "The dog genome comprises approximately 2.4 billion base pairs arranged in 38 pairs of "
          "autosomes plus the sex chromosomes (2n = 78) and contains roughly 19,000 protein-coding "
          "genes (Lindblad-Toh et al., 2005). Dogs show greater variation in body size than any other "
          "terrestrial mammal species: adult body mass ranges from about 1 kg in the smallest toy "
          "breeds to well over 100 kg in the largest mastiffs, a difference of roughly two orders of "
          "magnitude. A single variant at the IGF1 locus is a major determinant of small size across "
          "breeds (Sutter et al., 2007)."),
    ("p", "Roughly 350 breeds are recognized by the Fédération Cynologique Internationale, and most "
          "modern breeds were formalized within the last few centuries as kennel clubs and written "
          "breed standards emerged in the nineteenth century (Parker et al., 2017). Breed is a weaker "
          "predictor of individual behaviour than popular stereotypes suggest: in a study combining "
          "genomic data from thousands of dogs with owner-reported behavioural surveys, breed "
          "accounted for only about 9% of behavioural variation among individuals (Morrill et al., "
          "2022)."),

    ("h1", "4. Sensory Biology"),
    ("p", "Olfaction is the most striking of the canine senses. The human olfactory epithelium holds an "
          "estimated 5-6 million receptor cells, whereas commonly cited estimates for dogs range from "
          "about 125 million to 300 million depending on breed, and a proportionally larger part of "
          "the dog brain is devoted to olfactory processing (Table 1). Dogs also possess a "
          "vomeronasal organ and sniff in rapid bursts, which is thought to improve odorant sampling. "
          "Trained dogs are used to detect explosives, narcotics, and missing persons, and research "
          "has explored detection of disease-associated volatile compounds; reported accuracy for "
          "infections such as SARS-CoV-2 has varied considerably between studies and depends strongly "
          "on training and testing protocol."),
    ("table",
     "Table 1. Approximate sensory and physiological comparison of humans and dogs. Values are "
     "rounded and vary by breed and study."),
    ("p", "Dogs hear higher frequencies than humans, with an upper limit near 45 kHz compared with about "
          "20 kHz for humans (Heffner, 1983; Figure 2). Canine colour vision is dichromatic, with cone "
          "sensitivities near 429-435 nm and 555 nm, so dogs discriminate blues and yellows but "
          "confuse reds and greens (Neitz et al., 1989). Visual acuity is lower than in humans, on "
          "the order of 20/75 in Snellen terms, but dogs are well adapted to dim light and to "
          "detecting movement (Miller & Murphy, 1995)."),
    ("fig", "hearing",
     "Figure 2. Approximate hearing ranges of humans and dogs on a logarithmic frequency axis "
     "(dog values after Heffner, 1983)."),

    ("h1", "5. Cognition and Social Behaviour"),
    ("p", "Dogs are unusually skilled at reading human communicative signals. In object-choice tasks, "
          "dogs follow human pointing and gaze cues more skillfully than wolves or chimpanzees "
          "(Hare et al., 2002). When faced with an unsolvable problem, dogs, unlike socialized "
          "wolves, look back at a nearby human, a behaviour interpreted as a request for help "
          "(Miklósi et al., 2003)."),
    ("p", "A hormonal mechanism may reinforce this bond. Nagasawa et al. (2015) found that mutual "
          "gazing between dogs and their owners increased urinary oxytocin in both partners, whereas "
          "hand-raised wolves did not elicit the same response from their handlers, suggesting a "
          "positive feedback loop that may have helped shape human-dog attachment."),
    ("p", "Dogs can also learn large numbers of words. A border collie named Rico retrieved items "
          "correctly on the basis of more than 200 labels (Kaminski et al., 2004), and another border "
          "collie, Chaser, learned the names of 1,022 objects (Pilley & Reid, 2011). Estimates for "
          "typical dogs are far lower; Coren (2006) suggests an average of about 165 words and "
          "signals (Figure 3). Neuroimaging suggests that dog brains combine the lexical content and "
          "intonation of praise in reward-related regions (Andics et al., 2016)."),
    ("fig", "words",
     "Figure 3. Reported numbers of human words or signals comprehended. Values for Rico and Chaser "
     "come from single-animal studies; the estimate for typical dogs is from Coren (2006). The "
     "sources used different methods, so the bars are not directly comparable."),

    ("h1", "6. Health, Lifespan, and Welfare"),
    ("p", "Lifespan in dogs is inversely related to body size: small breeds commonly live 12-16 years, "
          "whereas giant breeds often live only 6-10 years (Figure 4). This is opposite to the positive "
          "size-longevity relationship seen across mammal species. Cancer is a leading cause of death "
          "in older dogs, and obesity is a widespread welfare problem, with surveys in some countries "
          "reporting that roughly half or more of pet dogs are overweight. Because companion dogs "
          "share human environments, large longitudinal studies such as the Dog Aging Project follow "
          "companion dogs to identify the determinants of healthy aging."),
    ("fig", "lifespan",
     "Figure 4. Approximate typical lifespan ranges by adult body-mass class. Ranges are rounded "
     "values compiled from commonly reported figures; individual breeds and studies vary."),
    ("p", "Dogs are also the source of most human rabies deaths: canine rabies is estimated to cause "
          "about 59,000 human deaths annually, mostly in Africa and Asia, although the disease is "
          "preventable through vaccination of dogs (Hampson et al., 2015). Global health partners "
          "have set a target of eliminating dog-mediated human rabies deaths by 2030."),

    ("h1", "7. Roles in Human Society"),
    ("p", "Dogs perform a wide range of functions, including herding and guarding livestock, assisting "
          "people with disabilities, detecting substances and disease, and participating in "
          "search-and-rescue. Beyond work, companion dogs are associated with benefits such as "
          "increased physical activity and reduced loneliness, although the evidence for health "
          "effects is mixed: many studies rely on self-report or cannot exclude selection effects, "
          "since people who choose to own dogs may differ from those who do not (Herzog, 2011). "
          "Free-ranging dogs can also threaten wildlife through predation, disturbance, disease "
          "transmission, and hybridization (Hughes & Macdonald, 2013)."),

    ("h1", "8. Limitations and Future Directions"),
    ("p", "Several limitations should be noted. Many cognitive studies use small samples of highly "
          "trained or pet dogs from Western societies, limiting generalization. Ancient DNA sampling "
          "is sparse for many regions and periods, so estimates of the timing and geography of "
          "domestication may change as new specimens are sequenced. Finally, quantities such as "
          "sensory thresholds and lifespans differ between studies, and the values presented here "
          "are approximate. Future work integrating ancient genomes, large-scale phenotyping, and "
          "long-term cohorts will be needed to clarify how dogs became such versatile partners."),

    ("h1", "9. Conclusion"),
    ("p", "Dogs are the product of a long biological and cultural partnership with humans. Their "
          "genomes, senses, and social minds have been shaped by that partnership, and they now "
          "serve as both valued companions and informative models for science. Continued research "
          "benefits not only our understanding of evolution and cognition but also the welfare of "
          "dogs and the people who live with them."),

    ("h1", "References"),
    ("ref", "Andics, A., Gábor, A., Gácsi, M., Faragó, T., Szabó, D., & Miklósi, Á. (2016). Neural mechanisms for lexical processing in dogs. Science, 353, 1030-1032."),
    ("ref", "Axelsson, E., et al. (2013). The genomic signature of dog domestication reveals adaptation to a starch-rich diet. Nature, 495, 360-364."),
    ("ref", "Bergström, A., et al. (2020). Origins and genetic legacy of prehistoric dogs. Science, 370, 557-564."),
    ("ref", "Coren, S. (2006). The Intelligence of Dogs (revised ed.). Free Press."),
    ("ref", "Frantz, L. A. F., et al. (2016). Genomic and archaeological evidence suggest a dual origin of domestic dogs. Science, 352, 1228-1231."),
    ("ref", "Hampson, K., et al. (2015). Estimating the global burden of endemic canine rabies. PLoS Neglected Tropical Diseases, 9, e0003709."),
    ("ref", "Hare, B., Brown, M., Williamson, C., & Tomasello, M. (2002). The domestication of social cognition in dogs. Science, 298, 1634-1636."),
    ("ref", "Heffner, H. E. (1983). Hearing in large and small dogs: absolute thresholds and size of the tympanic membrane. Behavioral Neuroscience, 97, 310-318."),
    ("ref", "Herzog, H. (2011). The impact of pets on human health and psychological well-being: fact, fiction, or hypothesis? Current Directions in Psychological Science, 20, 236-239."),
    ("ref", "Hughes, J., & Macdonald, D. W. (2013). A review of the interactions between free-roaming domestic dogs and wildlife. Biological Conservation, 157, 341-351."),
    ("ref", "Kaminski, J., Call, J., & Fischer, J. (2004). Word learning in a domestic dog: evidence for fast mapping. Science, 304, 1682-1683."),
    ("ref", "Lindblad-Toh, K., et al. (2005). Genome sequence, comparative analysis and haplotype structure of the domestic dog. Nature, 438, 803-819."),
    ("ref", "Miklósi, Á., et al. (2003). A simple reason for a big difference: wolves do not look back at humans, but dogs do. Current Biology, 13, 763-766."),
    ("ref", "Miller, P. E., & Murphy, C. J. (1995). Vision in dogs. Journal of the American Veterinary Medical Association, 207, 1623-1634."),
    ("ref", "Morrill, K., et al. (2022). Ancestry-inclusive dog genomics challenges popular breed stereotypes. Science, 376, eabk0639."),
    ("ref", "Nagasawa, M., et al. (2015). Oxytocin-gaze positive loop and the coevolution of human-dog bonds. Science, 348, 333-336."),
    ("ref", "Neitz, J., Geist, T., & Jacobs, G. H. (1989). Color vision in the dog. Visual Neuroscience, 3, 119-125."),
    ("ref", "Parker, H. G., et al. (2017). Genomic analyses reveal the influence of geographic origin, migration, and hybridization on modern dog breed development. Cell Reports, 19, 697-708."),
    ("ref", "Pilley, J. W., & Reid, A. K. (2011). Border collie comprehends object names as verbal referents. Behavioural Processes, 86, 184-195."),
    ("ref", "Sutter, N. B., et al. (2007). A single IGF1 allele is a major determinant of small size in dogs. Science, 316, 112-115."),
    ("ref", "Trut, L. N. (1999). Early canid domestication: the farm-fox experiment. American Scientist, 87, 160-169."),
    ("ref", "Wilkins, A. S., Wrangham, R. W., & Fitch, W. T. (2014). The domestication syndrome in mammals: a unified explanation based on neural crest cell behavior and genetics. Genetics, 197, 795-808."),
]

TABLE_1 = [
    ("Feature", "Human", "Dog"),
    ("Olfactory receptor cells", "~5-6 million", "~125-300 million (breed-dependent)"),
    ("Hearing range", "~20 Hz - 20 kHz", "~67 Hz - 45 kHz"),
    ("Colour vision", "Trichromatic", "Dichromatic"),
    ("Visual acuity (Snellen)", "20/20", "~20/75"),
    ("Normal body temperature", "36.5-37.5 °C", "38.3-39.2 °C"),
]

# ---- figures, drawn with plain tkinter canvas primitives (no extra libraries) ----
INK, GRID, BLUE, RUST = "#3b3128", "#e2dbcf", "#3a6ea5", "#a0521d"


def _fig_timeline(c, w, h):
    left, right, ay = 30, w - 30, 88
    X = lambda yrs: left + (5 - math.log10(yrs)) / 3 * (right - left)
    for t in (100, 1000, 10000, 100000):
        c.create_line(X(t), 15, X(t), h - 36, fill=GRID)
        c.create_text(X(t), h - 26, text=f"{t:,}", font=F("Helvetica", 9), fill=INK)
    c.create_text(w / 2, h - 10, text="Years before present (log scale)", font=F("Helvetica", 9), fill=INK)
    c.create_line(left, ay, right, ay, fill=INK, width=2)
    # range of dog-wolf divergence estimates
    x0, x1 = X(40000), X(20000)
    c.create_rectangle(x0, ay - 6, x1, ay + 6, fill=RUST, outline="")
    mid = (x0 + x1) / 2
    c.create_line(mid, ay + 6, mid, ay + 34, fill=INK)
    c.create_text(mid, ay + 36, anchor="n", justify="center", font=F("Helvetica", 9), fill=INK,
                  text="Dog-wolf divergence\n(est. 20,000-40,000)")
    # (years ago, label, vertical offset, side of text relative to the line)
    for yrs, label, dy, side in (
        (14200, "Bonn-Oberkassel\nburial (~14,200)", -38, "e"),
        (10000, "Koster, Illinois\nburials (~10,000)", 34, "w"),
        (5000, "Distinct types in\nEgyptian art (~5,000)", -38, "w"),
        (153, "UK Kennel Club\nfounded (1873)", 34, "e"),
    ):
        x = X(yrs)
        c.create_line(x, ay, x, ay + dy, fill=INK)
        c.create_oval(x - 4, ay - 4, x + 4, ay + 4, fill=BLUE, outline="white")
        anchor = ("s" if dy < 0 else "n") + side
        c.create_text(x + (4 if side == "w" else -4), ay + dy, anchor=anchor,
                      justify="right" if side == "e" else "left",
                      text=label, font=F("Helvetica", 9), fill=INK)


def _fig_hearing(c, w, h):
    left, right = 80, w - 30
    X = lambda f: left + (math.log10(f) - 1) / 4 * (right - left)
    for f, lab in ((10, "10"), (100, "100"), (1000, "1k"), (10000, "10k"), (100000, "100k")):
        c.create_line(X(f), 12, X(f), h - 40, fill=GRID)
        c.create_text(X(f), h - 28, text=lab, font=F("Helvetica", 9), fill=INK)
    c.create_text((left + right) / 2, h - 10, text="Frequency (Hz, log scale)", font=F("Helvetica", 9), fill=INK)
    for name, lo, hi, col, y in (("Human", 20, 20000, BLUE, 40), ("Dog", 67, 45000, RUST, 85)):
        c.create_text(left - 10, y, text=name, anchor="e", font=F("Helvetica", 10, "bold"), fill=INK)
        c.create_rectangle(X(lo), y - 14, X(hi), y + 14, fill=col, outline="")
        c.create_text(X(lo) + 8, y, anchor="w", font=F("Helvetica", 9), fill="white",
                      text=f"{lo} Hz - {hi / 1000:g} kHz")


def _fig_words(c, w, h):
    left, right, vmax = 150, w - 50, 1100
    X = lambda v: left + v / vmax * (right - left)
    for v in (0, 250, 500, 750, 1000):
        c.create_line(X(v), 10, X(v), h - 40, fill=GRID)
        c.create_text(X(v), h - 28, text=str(v), font=F("Helvetica", 9), fill=INK)
    c.create_text((left + right) / 2, h - 10, text="Words / signals comprehended", font=F("Helvetica", 9), fill=INK)
    for label, val, col, y in (("Typical dog\n(words + signals)", 165, BLUE, 32),
                               ("Rico\n(border collie)", 200, RUST, 72),
                               ("Chaser\n(border collie)", 1022, RUST, 112)):
        c.create_text(left - 10, y, text=label, anchor="e", justify="right", font=F("Helvetica", 9), fill=INK)
        c.create_rectangle(left, y - 13, X(val), y + 13, fill=col, outline="")
        c.create_text(X(val) + 6, y, text=f"{val:,}", anchor="w", font=F("Helvetica", 9, "bold"), fill=INK)


def _fig_lifespan(c, w, h):
    left, right, top, bottom, vmax = 60, w - 20, 15, h - 50, 18
    Y = lambda v: bottom - v / vmax * (bottom - top)
    for v in (0, 4, 8, 12, 16):
        c.create_line(left, Y(v), right, Y(v), fill=GRID)
        c.create_text(left - 8, Y(v), text=str(v), anchor="e", font=F("Helvetica", 9), fill=INK)
    c.create_text(16, (top + bottom) / 2, text="Typical lifespan (years)", angle=90, font=F("Helvetica", 9), fill=INK)
    classes = (("Toy\n(<5 kg)", 13, 16), ("Small\n(5-10 kg)", 12, 15), ("Medium\n(10-25 kg)", 10, 14),
               ("Large\n(25-45 kg)", 9, 12), ("Giant\n(>45 kg)", 6, 10))
    step = (right - left) / len(classes)
    for i, (label, lo, hi) in enumerate(classes):
        cx = left + (i + 0.5) * step
        c.create_rectangle(cx - 22, Y(hi), cx + 22, Y(lo), fill=RUST, outline="")
        c.create_text(cx, Y(hi) - 8, text=f"{lo}-{hi}", font=F("Helvetica", 9, "bold"), fill=INK)
        c.create_text(cx, bottom + 8, text=label, anchor="n", justify="center", font=F("Helvetica", 9), fill=INK)


FIGURES = {  # name -> (draw function, width, height)
    "timeline": (_fig_timeline, 520, 215),
    "hearing": (_fig_hearing, 520, 150),
    "words": (_fig_words, 520, 170),
    "lifespan": (_fig_lifespan, 520, 220),
}


# ---- Group chat content for the right-hand panel ----
DOG_CHANCE = 0.10   # 10% of messages mention dogs

SENDERS = {
    "Sam":    "#7fe0c3",
    "Priya":  "#9ad1ff",
    "Jordan": "#ffd479",
    "Mei":    "#f5a3c7",
    "Dave":   "#c3a6ff",
    "Alex":   "#ffb38a",
}

MUNDANE_MESSAGES = [
    "who's picking up milk?",
    "I think I left my charger at your place",
    "ugh, traffic is awful today",
    "anyone want to grab lunch?",
    "the wifi is down again",
    "did anyone watch that show last night?",
    "running 10 min late, sorry!",
    "can someone send me the address?",
    "it's so cold in the office",
    "I just burned my toast",
    "does anyone have a stapler?",
    "lol same",
    "wait what time is the meeting?",
    "forgot my umbrella, of course it's raining",
    "I need coffee. Now.",
    "we're out of paper towels",
    "is it recycling day or trash day?",
    "my phone is at 3%",
    "ok but what's for dinner",
    "just parked, be right there",
    "thanks!!",
    "haha good one",
    "did you see the weather forecast?",
    "I'm so tired today",
    "who took my leftovers from the fridge??",
    "can we move it to 3?",
    "brb",
    "just got home, finally",
    "the elevator is broken again",
    "anyone up for pizza tonight?",
    "I keep losing my keys",
    "yep, sounds good",
    "not sure, let me check",
    "someone left the lights on",
    "the printer is jammed. again.",
    "happy Friday everyone",
    "I'll bring snacks",
    "sorry, was in a meeting",
    "what's the wifi password again?",
    "ok I'm heading out",
]

DOG_MESSAGES = [
    "my dog just ate a whole sock",
    "walking the dog first, then I'll call you",
    "saw the cutest golden retriever at the park",
    "the dog is barking at the mail carrier again",
    "someone's puppy is in the lobby!!",
    "sorry, the dog ate my homework. literally.",
    "need to buy dog food on the way home",
    "my neighbor's dog is SO loud",
    "vet appointment for the dog at 4",
    "dog just stole my spot on the couch",
]


# Messages that come with a photo: (text, scene). The scene picks which built-in
# illustration is drawn when you haven't supplied your own photos.
PHOTO_CHANCE = 0.04        # everyday messages that include a photo
DOG_PHOTO_CHANCE = 0.25    # dog messages that include a photo
MIN_MESSAGES_BETWEEN_PHOTOS = 8   # never show two photos closer together than this

EVERYDAY_PHOTO_MESSAGES = [
    ("my coffee this morning", "coffee"),
    ("look at this sunset!", "sunset"),
    ("dinner tonight", "pizza"),
    ("this weather though", "rain"),
    ("best coffee ever", "coffee"),
    ("view from my window", "sunset"),
    ("lunch was pizza. again.", "pizza"),
    ("it has been like this all day", "rain"),
]

DOG_PHOTO_MESSAGES = [
    ("look who I met at the park!", "dog"),
    ("this is my dog", "dog"),
    ("he wants his ball. constantly.", "dog_ball"),
    ("someone's puppy in the lobby!!", "dog"),
    ("dog vs. ball. the ball is winning", "dog_ball"),
]

# ---------------------------------------------------------------------------
# YOUR PHOTOS GO HERE
#   PHOTOS_DIR/dogs/      -> photos shown in the dog-related messages
#   PHOTOS_DIR/everyday/  -> photos shown in the everyday messages
# Change PHOTOS_DIR to any folder you like (or use --photos on the command line).
# The subfolders are created automatically. New files are picked up while the
# app is running, so you can keep adding images without restarting.
# ---------------------------------------------------------------------------
PHOTOS_DIR = Path(__file__).resolve().parent / "media"
PHOTO_SUBFOLDERS = {"dog": "dogs", "everyday": "everyday"}
MAX_PHOTO_HEIGHT = 260      # tall photos are shrunk to fit this height (pixels)
RESCAN_MS = 5000            # how often to look for newly added photos

# Captions used when one of *your* photos is attached (the built-in captions
# like "look at this sunset!" would not match an arbitrary picture).
GENERIC_PHOTO_MESSAGES = {
    "dog": ["look at this dog!", "so cute", "meet the newest member", "had to share this one"],
    "everyday": ["check this out", "look at this!", "thought you'd like this",
                 "sent you a photo", "this made my day"],
}


def supported_extensions():
    """Pillow reads many formats; plain tkinter can only read PNG and GIF."""
    if Image is not None:
        return {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
    return {".png", ".gif"}


def scan_photos(base):
    """Create the photo folders if needed and return {category: [image paths]}."""
    exts = supported_extensions()
    found = {}
    for category, sub in PHOTO_SUBFOLDERS.items():
        folder = Path(base) / sub
        try:
            folder.mkdir(parents=True, exist_ok=True)
            found[category] = sorted(
                p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts
            )
        except OSError:
            found[category] = []
    return found


# ---- tiny dependency-free "photo" generator built on tk.PhotoImage ----
def _rect(img, x0, y0, x1, y1, color):
    w, h = img.width(), img.height()
    x0, x1 = max(0, int(x0)), min(w, int(x1))
    y0, y1 = max(0, int(y0)), min(h, int(y1))
    if x1 > x0 and y1 > y0:
        img.put(color, to=(x0, y0, x1, y1))


def _circle(img, cx, cy, r, color):
    for dy in range(-int(r), int(r) + 1):
        dx = int(math.sqrt(max(r * r - dy * dy, 0)))
        _rect(img, cx - dx, cy + dy, cx + dx + 1, cy + dy + 1, color)


def _lerp(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _gradient(img, y0, y1, top, bottom):
    for y in range(int(y0), int(y1)):
        _rect(img, 0, y, img.width(), y + 1, _lerp(top, bottom, (y - y0) / max(y1 - y0 - 1, 1)))


def _draw_dog(img, cx, gy, u, fur, ball=False):
    dark = _lerp(fur, "#000000", 0.35)
    _rect(img, cx - 5 * u, gy - 6.2 * u, cx - 4 * u, gy - 3.4 * u, fur)        # tail
    _rect(img, cx - 4 * u, gy - 5 * u, cx + 3 * u, gy - 2 * u, fur)            # body
    for lx in (-3.8, -2.6, 0.9, 2.1):                                          # legs
        _rect(img, cx + lx * u, gy - 2 * u, cx + (lx + 0.9) * u, gy, fur)
    _rect(img, cx + 2 * u, gy - 7.4 * u, cx + 5 * u, gy - 4.2 * u, fur)        # head
    _rect(img, cx + 4.6 * u, gy - 5.8 * u, cx + 6.3 * u, gy - 4.2 * u, "#f3e2c7")  # snout
    _rect(img, cx + 5.7 * u, gy - 5.9 * u, cx + 6.4 * u, gy - 5.2 * u, "#1c1c1c")  # nose
    _rect(img, cx + 1.8 * u, gy - 7.4 * u, cx + 2.9 * u, gy - 5.0 * u, dark)   # ear
    _rect(img, cx + 3.9 * u, gy - 6.5 * u, cx + 4.5 * u, gy - 5.9 * u, "#1c1c1c")  # eye
    if ball:
        _circle(img, cx + 8.6 * u, gy - 1.0 * u, 1.0 * u, "#e63946")
        _circle(img, cx + 8.3 * u, gy - 1.4 * u, 0.35 * u, "#ff9aa2")


def make_placeholder_photo(scene, w):
    """Draw a small illustration for `scene` and return a tk.PhotoImage."""
    h = int(w * 0.65)
    img = tk.PhotoImage(width=w, height=h)
    u = w / 20.0

    if scene in ("dog", "dog_ball"):
        horizon = h * 0.62
        _gradient(img, 0, horizon, "#8fd3ff", "#e3f6ff")
        _circle(img, w * 0.84, h * 0.2, u * 1.6, "#ffe066")
        _gradient(img, horizon, h, "#5cb85c", "#3c8d3c")
        fur = random.choice(["#b5651d", "#d9a441", "#4a3b32", "#e8e0d0", "#8a8a8a"])
        _draw_dog(img, w * 0.36, h * 0.9, u, fur, ball=(scene == "dog_ball"))
    elif scene == "coffee":
        _rect(img, 0, 0, w, h, "#f1e3cf")
        _rect(img, 0, h * 0.78, w, h, "#b98a5c")                               # table
        cx, top, cw, ch = w * 0.5, h * 0.36, w * 0.28, h * 0.42
        _rect(img, cx - cw / 2, top, cx + cw / 2, top + ch, "#ffffff")         # cup
        _rect(img, cx - cw / 2, top, cx + cw / 2, top + ch * 0.22, "#5a3a22")  # coffee
        _rect(img, cx + cw / 2, top + ch * 0.2, cx + cw / 2 + u, top + ch * 0.7, "#ffffff")
        _rect(img, cx - cw, top + ch, cx + cw, top + ch + h * 0.05, "#e6e6e6")  # saucer
        for sx in (-0.2, 0.0, 0.2):                                            # steam
            _rect(img, cx + sx * cw, top - h * 0.22, cx + sx * cw + u * 0.5, top - h * 0.04, "#d8cbb8")
    elif scene == "sunset":
        _gradient(img, 0, h * 0.7, "#5b3a8c", "#ff9a5a")
        _circle(img, w * 0.5, h * 0.66, u * 2.6, "#ffd166")
        _rect(img, 0, h * 0.7, w, h, "#241b2f")                                # ground
        _rect(img, w * 0.12, h * 0.55, w * 0.16, h * 0.7, "#241b2f")           # tree trunk
        _circle(img, w * 0.14, h * 0.5, u * 1.2, "#241b2f")
    elif scene == "pizza":
        _rect(img, 0, 0, w, h, "#b23a3a")
        for i in range(0, w, int(u * 2)):                                      # checker cloth
            _rect(img, i, 0, i + u, h, "#c94c4c")
        cx, cy, r = w * 0.5, h * 0.5, h * 0.42
        _circle(img, cx, cy, r, "#d9a45b")
        _circle(img, cx, cy, r * 0.88, "#f4c542")
        for ox, oy in ((-0.4, -0.3), (0.3, -0.35), (0.0, 0.05), (-0.35, 0.4), (0.4, 0.3)):
            _circle(img, cx + ox * r, cy + oy * r, r * 0.16, "#c1121f")
    else:  # rain
        _gradient(img, 0, h, "#6c7a89", "#aeb9c4")
        for cx, cy, r in ((0.3, 0.3, 1.6), (0.45, 0.24, 2.0), (0.62, 0.3, 1.7), (0.5, 0.34, 1.8)):
            _circle(img, w * cx, h * cy, u * r, "#e8edf1")
        for _ in range(26):
            x, y = random.randint(0, w - 3), random.randint(int(h * 0.45), h - 12)
            _rect(img, x, y, x + 2, y + 10, "#4a90d9")
    return img


class DogApp(tk.Tk):
    STREAM_SPEED_PX = 1      # pixels moved per frame
    STREAM_DELAY_MS = 30     # milliseconds between frames
    STREAM_GAP = 22          # vertical gap between chat bubbles

    def __init__(self, photos_dir=PHOTOS_DIR):
        super().__init__()
        self.photos_dir = Path(photos_dir).expanduser().resolve()
        self.title("All About Dogs")
        self.geometry("1100x650")
        self.minsize(700, 400)

        # 80 / 20 split. `uniform` forces the exact ratio regardless of content.
        self.columnconfigure(0, weight=80, uniform="cols")
        self.columnconfigure(1, weight=20, uniform="cols")
        self.rowconfigure(0, weight=1)

        self._build_article_panel()
        self._build_stream_panel()

        self.msg_tags = []              # one canvas tag per chat message
        self.msg_counter = 0
        self.last_sender = None
        self.since_photo = 0            # messages since the last photo
        self.photo_refs = {}            # tag -> image (prevents garbage collection)
        self.user_photos = scan_photos(self.photos_dir)
        self._report_photos()
        self.after(RESCAN_MS, self._rescan_photos)
        for seq in ("<Control-plus>", "<Control-equal>", "<Control-KP_Add>"):
            self.bind(seq, lambda e: self._zoom(+0.1))
        for seq in ("<Control-minus>", "<Control-KP_Subtract>"):
            self.bind(seq, lambda e: self._zoom(-0.1))
        self.bind("<Control-0>", lambda e: self._zoom(None))
        self.after(100, self._prime_stream)
        self.after(150, self._tick)

    # ------------------------------------------------------------------ left
    def _build_article_panel(self):
        frame = tk.Frame(self, bg="#fdf8f0")
        self.article_frame = frame
        frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        text = tk.Text(
            frame, wrap="word", bg="#fdf8f0", fg="#2b2118",
            font=F("Georgia", 12), padx=40, pady=30, relief="flat",
            spacing2=3, spacing3=8, cursor="arrow", borderwidth=0,
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.article = text

        serif = "Georgia"
        text.tag_configure("title", font=F(serif, 20, "bold"), justify="center", spacing3=6, foreground="#2b2118")
        text.tag_configure("subtitle", font=F(serif, 12, "italic"), justify="center", spacing3=16, foreground="#6b5b4b")
        text.tag_configure("abstract", font=F(serif, 11), lmargin1=30, lmargin2=30, rmargin=30, spacing3=6)
        text.tag_configure("abstract_head", font=F(serif, 11, "bold"), lmargin1=30, lmargin2=30, spacing1=6)
        text.tag_configure("keywords", font=F(serif, 10, "italic"), lmargin1=30, lmargin2=30, spacing3=10)
        text.tag_configure("h1", font=F(serif, 14, "bold"), foreground="#7a3e12", spacing1=16, spacing3=6)
        text.tag_configure("p", font=F(serif, 12), spacing3=8)
        text.tag_configure("cap", font=F(serif, 10), lmargin1=20, lmargin2=20, rmargin=20, spacing3=14, foreground="#4a3f34")
        text.tag_configure("capbold", font=F(serif, 10, "bold"), foreground="#4a3f34")
        text.tag_configure("tablecap", font=F(serif, 10), lmargin1=20, lmargin2=20, rmargin=20, spacing1=6, spacing3=4, foreground="#4a3f34")
        text.tag_configure("ref", font=F(serif, 10), lmargin1=0, lmargin2=24, spacing3=4)
        text.tag_configure("center", justify="center")

        for block in ARTICLE:
            kind = block[0]
            if kind == "abstract":
                text.insert("end", "Abstract\n", "abstract_head")
                text.insert("end", block[1] + "\n", "abstract")
            elif kind == "keywords":
                text.insert("end", "Keywords: " + block[1] + "\n", "keywords")
            elif kind == "fig":
                draw, fw, fh = FIGURES[block[1]]
                canvas = tk.Canvas(text, width=int(fw * FONT_SCALE), height=int(fh * FONT_SCALE),
                                   bg="#ffffff", highlightthickness=1, highlightbackground="#cfc6b8")
                draw(canvas, fw, fh)
                canvas.scale("all", 0, 0, FONT_SCALE, FONT_SCALE)
                self._embed(canvas)
                self._caption(block[2], "cap")
            elif kind == "table":
                self._caption(block[1], "tablecap")
                self._embed(self._make_table(text))
                text.insert("end", "\n", "cap")
            else:
                text.insert("end", block[1] + "\n", kind)

        text.configure(state="disabled")   # read-only

    def _zoom(self, delta=None):
        """Ctrl +/-/0: change the text size of the article and the chat on the fly."""
        global FONT_SCALE
        FONT_SCALE = DEFAULT_SCALE if delta is None else min(3.0, max(0.7, round(FONT_SCALE + delta, 2)))
        top = self.article.yview()[0]
        self.article_frame.destroy()
        self._build_article_panel()
        self.article.yview_moveto(top)
        # restart the chat so its bubbles use the new size too
        self.canvas.delete("all")
        self.msg_tags.clear()
        self.photo_refs.clear()
        self._prime_stream()
        self.title(f"All About Dogs  (text size {int(FONT_SCALE * 100)}%)")

    def _caption(self, caption, tag):
        label, rest = caption.split(". ", 1)
        self.article.insert("end", label + ". ", "capbold")
        self.article.insert("end", rest + "\n", tag)

    def _embed(self, widget):
        """Place a widget on its own centered line inside the article."""
        text = self.article
        start = text.index("end-1c")
        text.window_create("end", window=widget, pady=6)
        text.insert("end", "\n")
        text.tag_add("center", start, "end-1c")
        self._forward_wheel(widget)

    def _make_table(self, parent):
        frame = tk.Frame(parent, bg="#cfc6b8")
        widths = (20, 14, 26)
        for r, row in enumerate(TABLE_1):
            for col, value in enumerate(row):
                head = r == 0
                tk.Label(frame, text=value, width=widths[col], anchor="w", padx=6, pady=4,
                         bg="#efe6d6" if head else "#ffffff", fg="#2b2118",
                         font=F("Georgia", 10, "bold" if head else "normal")
                         ).grid(row=r, column=col, padx=1, pady=1, sticky="nsew")
        return frame

    def _forward_wheel(self, widget):
        """Mouse wheel over a figure/table should still scroll the article."""
        def wheel(event):
            up = getattr(event, "delta", 0) > 0 or event.num == 4
            self.article.yview_scroll(-3 if up else 3, "units")
            return "break"
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            widget.bind(seq, wheel)
        for child in widget.winfo_children():
            self._forward_wheel(child)

    # ----------------------------------------------------------------- right
    def _build_stream_panel(self):
        self.canvas = tk.Canvas(self, bg="#101820", highlightthickness=0)
        self.canvas.grid(row=0, column=1, sticky="nsew")

    def _pick_message(self):
        """Pick a message, retrying so the same text never repeats back-to-back."""
        for _ in range(10):
            text, spec = self._roll_message()
            if text != getattr(self, 'last_text', None):
                break
        self.last_text = text
        return text, spec

    def _roll_message(self):
        """Return (text, photo_spec). ~10% of messages are dog-related; some have photos.

        photo_spec is None, or (category, scene).
        """
        is_dog = random.random() < DOG_CHANCE
        wants_photo = random.random() < (DOG_PHOTO_CHANCE if is_dog else PHOTO_CHANCE)
        # Keep photos rare: enforce a cool-down after each one.
        self.since_photo += 1
        if wants_photo and self.since_photo <= MIN_MESSAGES_BETWEEN_PHOTOS:
            wants_photo = False
        if wants_photo:
            self.since_photo = 0
        if is_dog:
            if wants_photo:
                return self._photo_message("dog", DOG_PHOTO_MESSAGES)
            return random.choice(DOG_MESSAGES), None
        if wants_photo:
            return self._photo_message("everyday", EVERYDAY_PHOTO_MESSAGES)
        return random.choice(MUNDANE_MESSAGES), None

    def _photo_message(self, category, pool):
        text, scene = random.choice(pool)
        if self.user_photos.get(category):          # your own photo -> generic caption
            text = random.choice(GENERIC_PHOTO_MESSAGES[category])
        return text, (category, scene)

    def _report_photos(self):
        n_dog, n_day = len(self.user_photos["dog"]), len(self.user_photos["everyday"])
        print(f"Photos folder: {self.photos_dir}")
        print(f"  dogs/     {n_dog} image(s)" + ("" if n_dog else "  (using built-in illustrations)"))
        print(f"  everyday/ {n_day} image(s)" + ("" if n_day else "  (using built-in illustrations)"))
        if Image is None:
            print("  Tip: install Pillow (pip install pillow) to use JPG/WebP/BMP files too.")

    def _rescan_photos(self):
        """Pick up images added to the folders while the app is running."""
        self.user_photos = scan_photos(self.photos_dir)
        self.after(RESCAN_MS, self._rescan_photos)

    def _make_photo(self, spec, width):
        """Return your own photo if the category folder has any, else a built-in illustration."""
        category, scene = spec
        paths = self.user_photos.get(category)
        if paths:
            path = random.choice(paths)
            try:
                if Image is not None:
                    pil = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
                    scale = min(width / pil.width, MAX_PHOTO_HEIGHT / pil.height)
                    size = (max(int(pil.width * scale), 1), max(int(pil.height * scale), 1))
                    return ImageTk.PhotoImage(pil.resize(size, Image.LANCZOS))
                img = tk.PhotoImage(file=str(path))          # PNG/GIF without Pillow
                factor = max(math.ceil(img.width() / width),
                             math.ceil(img.height() / MAX_PHOTO_HEIGHT), 1)
                return img.subsample(factor) if factor > 1 else img
            except Exception:
                pass                                          # unreadable file -> fall back
        return make_placeholder_photo(scene, width)

    def _pick_sender(self):
        """Random sender, avoiding the same person twice in a row."""
        choices = [s for s in SENDERS if s != self.last_sender]
        self.last_sender = random.choice(choices)
        return self.last_sender

    def _add_message(self, y):
        """Draw one chat bubble at vertical position y; return its bottom edge."""
        canvas_w = max(self.canvas.winfo_width(), 100)
        sender = self._pick_sender()
        text, photo_spec = self._pick_message()
        tag = f"msg{self.msg_counter}"
        self.msg_counter += 1

        name_id = self.canvas.create_text(
            18, y, anchor="nw", text=sender, tags=tag,
            fill=SENDERS[sender], font=F("Helvetica", 14, "bold"),
        )
        name_bbox = self.canvas.bbox(name_id)

        text_id = self.canvas.create_text(
            18, name_bbox[3] + 3, anchor="nw", tags=tag,
            width=max(canvas_w - 44, 60), text=text,
            fill="#ffffff", font=F("Helvetica", 15),
        )
        bottom = self.canvas.bbox(text_id)[3]

        if photo_spec:
            photo_w = min(max(canvas_w - 36, 80), 360)
            photo = self._make_photo(photo_spec, photo_w)
            self.photo_refs[tag] = photo
            self.canvas.create_image(18, bottom + 8, anchor="nw", image=photo, tags=tag)
            bottom += 8 + photo.height()

        bubble = self.canvas.create_rectangle(
            8, y - 8, canvas_w - 8, bottom + 10,
            fill="#1f2c38", outline="", tags=tag,
        )
        self.canvas.tag_lower(bubble, name_id)   # bubble behind its text

        self.msg_tags.append(tag)
        return self.canvas.bbox(tag)[3]

    def _prime_stream(self):
        """Fill the panel initially so it doesn't start empty."""
        if self.msg_tags:            # already filled (e.g. by an earlier zoom)
            return
        if self.canvas.winfo_width() < 50:      # window not laid out yet: try again shortly
            self.after(50, self._prime_stream)
            return
        h = self.canvas.winfo_height()
        y = 10
        while y < h + 50:
            y = self._add_message(y) + self.STREAM_GAP

    def _tick(self):
        if not self.msg_tags:                   # waiting for the initial fill
            self.after(self.STREAM_DELAY_MS, self._tick)
            return
        # Scroll every message upward.
        for tag in self.msg_tags:
            self.canvas.move(tag, 0, -self.STREAM_SPEED_PX)

        # Drop messages that have fully scrolled off the top.
        while self.msg_tags:
            bbox = self.canvas.bbox(self.msg_tags[0])
            if bbox and bbox[3] < 0:
                old = self.msg_tags.pop(0)
                self.canvas.delete(old)
                self.photo_refs.pop(old, None)
            else:
                break

        # Post a new message whenever there's room below the last one.
        h = self.canvas.winfo_height()
        last_bottom = self.canvas.bbox(self.msg_tags[-1])[3] if self.msg_tags else 0
        if last_bottom + self.STREAM_GAP < h + 40:
            self._add_message(max(last_bottom + self.STREAM_GAP, h))

        self.after(self.STREAM_DELAY_MS, self._tick)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dog article + group chat viewer")
    parser.add_argument("--photos", default=str(PHOTOS_DIR),
                        help="folder containing 'dogs' and 'everyday' subfolders of images")
    parser.add_argument("--scale", type=float, default=FONT_SCALE,
                        help="text size multiplier, e.g. 1.5 (default %(default)s)")
    args = parser.parse_args()
    FONT_SCALE = DEFAULT_SCALE = args.scale
    DogApp(args.photos).mainloop()
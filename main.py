import asyncio
import json
import math
import random
import re
from datetime import datetime
from pathlib import Path

import edge_tts
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import AudioFileClip, VideoClip


# ==================================================
# MEDIAFLOW V3
# Story-driven Animated YouTube Shorts Generator
# ==================================================

WIDTH = 720
HEIGHT = 1280
FPS = 24
VOICE = "en-US-GuyNeural"

AUDIO_DIR = Path("output/audio")
VIDEO_DIR = Path("output/video")
SCRIPT_DIR = Path("output")

for folder in (AUDIO_DIR, VIDEO_DIR, SCRIPT_DIR):
    folder.mkdir(parents=True, exist_ok=True)


# ==================================================
# STORIES
# Each scene has its own environment and illustration.
# ==================================================

STORIES = [
    {
        "title": "The Power of Small Habits",
        "text": (
            "You do not need to change your entire life in one day. "
            "Start with one small habit. Read one page, walk for five "
            "minutes, or learn one new thing. Small actions may seem "
            "insignificant at first, but repeated consistently, "
            "they can create meaningful change. Progress is built "
            "one step at a time."
        ),
        "scenes": [
            {
                "headline": "A NEW DAY",
                "kind": "moon",
                "bg": "night",
            },
            {
                "headline": "START SMALL",
                "kind": "stairs",
                "bg": "mountain",
            },
            {
                "headline": "KEEP LEARNING",
                "kind": "book",
                "bg": "library",
            },
            {
                "headline": "TIME MATTERS",
                "kind": "clock",
                "bg": "city",
            },
            {
                "headline": "GROW EVERY DAY",
                "kind": "plant",
                "bg": "garden",
            },
            {
                "headline": "ONE STEP AT A TIME",
                "kind": "sun",
                "bg": "sunrise",
            },
        ],
    },
    {
        "title": "Why the Ocean Looks Blue",
        "text": (
            "Have you ever wondered why the ocean looks blue? "
            "Water absorbs colors from sunlight differently. "
            "Red light is absorbed more quickly, while blue light "
            "travels deeper and is scattered back toward our eyes. "
            "That is why large bodies of water often appear blue. "
            "Nature is full of fascinating surprises."
        ),
        "scenes": [
            {
                "headline": "LIGHT MEETS WATER",
                "kind": "sun",
                "bg": "sunrise",
            },
            {
                "headline": "A WORLD OF BLUE",
                "kind": "waves",
                "bg": "ocean",
            },
            {
                "headline": "COLORS OF LIGHT",
                "kind": "rays",
                "bg": "light",
            },
            {
                "headline": "DEEPER INTO THE SEA",
                "kind": "fish",
                "bg": "underwater",
            },
            {
                "headline": "BLUE LIGHT RETURNS",
                "kind": "rays",
                "bg": "deepsea",
            },
            {
                "headline": "NATURE IS AMAZING",
                "kind": "waves",
                "bg": "coast",
            },
        ],
    },
    {
        "title": "Your Brain Needs Sleep",
        "text": (
            "Sleep is not simply a break from being awake. "
            "While you sleep, your brain processes information, "
            "supports memory, and helps your body recover. "
            "Consistently missing sleep can affect concentration "
            "and mood. Remember that rest is part of the work."
        ),
        "scenes": [
            {
                "headline": "TIME TO REST",
                "kind": "moon",
                "bg": "night",
            },
            {
                "headline": "YOUR BRAIN STAYS BUSY",
                "kind": "brain",
                "bg": "brainroom",
            },
            {
                "headline": "MEMORIES FORM",
                "kind": "memory",
                "bg": "memory",
            },
            {
                "headline": "RECOVERY MATTERS",
                "kind": "plant",
                "bg": "garden",
            },
            {
                "headline": "RECHARGE YOURSELF",
                "kind": "sun",
                "bg": "sunrise",
            },
            {
                "headline": "REST IS PRODUCTIVE",
                "kind": "moon",
                "bg": "dawn",
            },
        ],
    },
]


# ==================================================
# FONTS
# ==================================================

def load_font(size, bold=True):
    if bold:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]
    else:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]

    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


FONT_TITLE = load_font(42)
FONT_CAPTION = load_font(30)
FONT_SMALL = load_font(20)
FONT_LABEL = load_font(17)


# ==================================================
# TEXT HELPERS
# ==================================================

def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        box = draw.textbbox((0, 0), candidate, font=font)

        if box[2] - box[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def draw_centered(
    draw,
    text,
    y,
    font,
    fill,
    max_width=620,
):
    lines = wrap_text(draw, text, font, max_width)
    line_height = font.size + 10

    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        x = (WIDTH - (box[2] - box[0])) // 2

        draw.text(
            (x + 2, y + 3),
            line,
            font=font,
            fill=(0, 0, 0, 150),
        )

        draw.text(
            (x, y),
            line,
            font=font,
            fill=fill,
        )

        y += line_height

    return y


def split_captions(text, max_words=5):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    captions = []

    for sentence in sentences:
        words = sentence.split()

        for i in range(0, len(words), max_words):
            phrase = " ".join(words[i:i + max_words])

            if phrase:
                captions.append(phrase)

    return captions


# ==================================================
# BACKGROUND ENVIRONMENTS
# ==================================================

PALETTES = {
    "night": (
        (8, 14, 42),
        (38, 28, 85),
    ),
    "mountain": (
        (30, 35, 85),
        (105, 65, 130),
    ),
    "library": (
        (35, 23, 58),
        (90, 48, 90),
    ),
    "city": (
        (15, 30, 65),
        (80, 55, 115),
    ),
    "garden": (
        (12, 48, 57),
        (30, 110, 105),
    ),
    "sunrise": (
        (90, 35, 75),
        (245, 145, 90),
    ),
    "ocean": (
        (5, 35, 80),
        (10, 115, 165),
    ),
    "light": (
        (20, 25, 75),
        (80, 65, 145),
    ),
    "underwater": (
        (2, 25, 65),
        (0, 100, 145),
    ),
    "deepsea": (
        (2, 10, 35),
        (5, 45, 95),
    ),
    "coast": (
        (20, 80, 120),
        (100, 160, 190),
    ),
    "brainroom": (
        (35, 15, 65),
        (105, 35, 100),
    ),
    "memory": (
        (20, 20, 65),
        (85, 50, 125),
    ),
    "dawn": (
        (35, 35, 85),
        (155, 105, 145),
    ),
}


def make_background(name, t):
    top, bottom = PALETTES[name]

    gradient = np.linspace(
        0,
        1,
        HEIGHT,
        dtype=np.float32,
    )[:, None, None]

    top_array = np.array(top, dtype=np.float32)
    bottom_array = np.array(bottom, dtype=np.float32)

    background = (
        top_array + (bottom_array - top_array) * gradient
    )

    background = np.repeat(background, WIDTH, axis=1)

    # Subtle animated light movement.
    glow_x = int(WIDTH * (0.5 + 0.22 * math.sin(t * 0.25)))
    glow_y = int(HEIGHT * 0.30)

    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]

    distance = np.sqrt(
        ((xx - glow_x) / 1.5) ** 2
        + (yy - glow_y) ** 2
    )

    glow = np.maximum(0, 1 - distance / 420) * 16

    background[:, :, 0] += glow * 0.45
    background[:, :, 1] += glow * 0.35
    background[:, :, 2] += glow

    return np.clip(background, 0, 255).astype(np.uint8)


def draw_environment(draw, name, t):
    """Draw a different environment for each scene."""

    if name in ("night", "dawn"):
        # Moonlit landscape.
        draw.ellipse(
            (510, 135, 610, 235),
            fill=(255, 225, 160, 255),
        )

        draw.polygon(
            [
                (0, 670),
                (130, 450),
                (250, 670),
                (400, 470),
                (570, 690),
                (720, 500),
                (720, 820),
                (0, 820),
            ],
            fill=(24, 28, 65, 255),
        )

        draw.polygon(
            [
                (0, 760),
                (180, 610),
                (330, 780),
                (500, 620),
                (720, 760),
                (720, 900),
                (0, 900),
            ],
            fill=(13, 23, 53, 255),
        )

    elif name == "mountain":
        # Climbing landscape.
        draw.polygon(
            [
                (0, 770),
                (140, 490),
                (290, 740),
                (440, 410),
                (720, 780),
                (720, 920),
                (0, 920),
            ],
            fill=(55, 75, 145, 255),
        )

        draw.polygon(
            [
                (440, 410),
                (385, 500),
                (445, 475),
                (490, 530),
            ],
            fill=(225, 225, 250, 255),
        )

        for i in range(5):
            x = 50 + i * 145
            y = 900 + int(5 * math.sin(t + i))
            draw.ellipse(
                (x, y, x + 8, y + 8),
                fill=(240, 240, 255, 150),
            )

    elif name == "library":
        # Tall bookshelves.
        for i in range(5):
            x = 35 + i * 145

            draw.rectangle(
                (x, 360, x + 110, 790),
                fill=(48, 26, 67, 255),
                outline=(200, 155, 110, 220),
                width=3,
            )

            for j in range(5):
                bx = x + 8 + j * 18
                by = 385 + (j % 2) * 8

                draw.rectangle(
                    (bx, by, bx + 13, 470 + j * 3),
                    fill=(
                        95 + j * 12,
                        55 + j * 8,
                        120 + j * 10,
                        255,
                    ),
                )

            draw.line(
                (x, 520, x + 110, 520),
                fill=(200, 155, 110, 255),
                width=5,
            )

            draw.line(
                (x, 650, x + 110, 650),
                fill=(200, 155, 110, 255),
                width=5,
            )

    elif name == "city":
        # Animated skyline.
        for i in range(7):
            x = i * 110
            height = 180 + (i % 3) * 65
            top = 760 - height

            draw.rectangle(
                (x, top, x + 85, 900),
                fill=(22, 27, 67, 255),
            )

            for wx in range(x + 12, x + 72, 22):
                for wy in range(top + 18, 850, 36):
                    brightness = 90 + int(
                        35 * abs(math.sin(t + wx + wy))
                    )

                    draw.rectangle(
                        (wx, wy, wx + 8, wy + 12),
                        fill=(255, 205, brightness, 255),
                    )

    elif name in ("ocean", "coast"):
        # Horizon and moving waves.
        draw.rectangle(
            (0, 480, WIDTH, 900),
            fill=(8, 75, 130, 255),
        )

        for row in range(9):
            y = 500 + row * 42
            points = []

            for x in range(0, WIDTH + 10, 10):
                yy = int(
                    y + math.sin(x * 0.025 + t * 1.5 + row) * 12
                )
                points.append((x, yy))

            draw.line(
                points,
                fill=(
                    55 + row * 5,
                    150 + row * 7,
                    220 + row * 3,
                    210,
                ),
                width=4,
            )

        if name == "coast":
            draw.polygon(
                [
                    (0, 780),
                    (220, 710),
                    (370, 810),
                    (520, 730),
                    (720, 800),
                    (720, 900),
                    (0, 900),
                ],
                fill=(210, 185, 135, 255),
            )

    elif name == "underwater":
        # Depth layers and underwater light beams.
        for i in range(5):
            x = 50 + i * 150 + int(math.sin(t + i) * 12)

            draw.polygon(
                [
                    (x, 350),
                    (x + 35, 350),
                    (x + 100, 880),
                    (x + 60, 880),
                ],
                fill=(65, 165, 220, 35),
            )

        for i in range(18):
            x = (i * 47 + int(t * 12)) % WIDTH
            y = (i * 61 - int(t * 25)) % 850

            draw.ellipse(
                (x, y, x + 5, y + 5),
                fill=(180, 230, 255, 150),
            )

    elif name == "deepsea":
        # Dark seabed.
        draw.polygon(
            [
                (0, 810),
                (160, 760),
                (280, 825),
                (470, 745),
                (720, 820),
                (720, 900),
                (0, 900),
            ],
            fill=(8, 24, 60, 255),
        )

        for i in range(12):
            x = (i * 57 + int(t * 9)) % WIDTH
            y = (i * 83 - int(t * 20)) % 850

            draw.ellipse(
                (x, y, x + 4, y + 4),
                fill=(120, 190, 255, 170),
            )

    elif name == "garden":
        # Ground and plants.
        draw.rectangle(
            (0, 820, WIDTH, 900),
            fill=(20, 75, 60, 255),
        )

        for i in range(9):
            x = i * 90 + 15
            sway = int(math.sin(t * 1.5 + i) * 8)

            draw.line(
                (x, 820, x + sway, 735),
                fill=(80, 200, 125, 255),
                width=7,
            )

            draw.ellipse(
                (x - 25 + sway, 760, x + sway, 780),
                fill=(80, 200, 125, 255),
            )

    elif name == "sunrise":
        # Glowing sunrise.
        sun_x = int(WIDTH * 0.5)
        sun_y = 470 + int(8 * math.sin(t * 0.4))

        draw.ellipse(
            (
                sun_x - 100,
                sun_y - 100,
                sun_x + 100,
                sun_y + 100,
            ),
            fill=(255, 210, 130, 255),
        )

        draw.rectangle(
            (0, 580, WIDTH, 900),
            fill=(100, 65, 105, 255),
        )

        draw.polygon(
            [
                (0, 760),
                (170, 650),
                (330, 780),
                (500, 640),
                (720, 750),
                (720, 900),
                (0, 900),
            ],
            fill=(45, 48, 90, 255),
        )

    elif name == "light":
        # Floating light streaks.
        for i in range(12):
            y = 380 + i * 35
            offset = int(math.sin(t + i * 0.5) * 55)

            draw.line(
                (
                    70 + offset,
                    y,
                    650 - offset,
                    y - 25,
                ),
                fill=(120, 180, 255, 100),
                width=3,
            )

    elif name == "brainroom":
        # Abstract neural network.
        nodes = []

        for i in range(12):
            x = 65 + (i * 53) % 600
            y = 380 + (i * 71) % 430

            x += int(math.sin(t + i) * 12)
            y += int(math.cos(t + i) * 12)

            nodes.append((x, y))

        for i, point in enumerate(nodes):
            for other in nodes[i + 1:]:
                if (
                    (point[0] - other[0]) ** 2
                    + (point[1] - other[1]) ** 2
                ) < 200 ** 2:
                    draw.line(
                        (point, other),
                        fill=(170, 110, 255, 65),
                        width=2,
                    )

        for x, y in nodes:
            draw.ellipse(
                (x - 7, y - 7, x + 7, y + 7),
                fill=(220, 185, 255, 230),
            )

    elif name == "memory":
        # Floating memory cards.
        for i in range(5):
            x = 55 + i * 135
            y = 450 + int(math.sin(t * 1.4 + i) * 22)

            draw.rounded_rectangle(
                (x, y, x + 100, y + 145),
                radius=14,
                fill=(105, 90, 180, 170),
                outline=(210, 205, 255, 220),
                width=3,
            )

            draw.ellipse(
                (x + 30, y + 25, x + 70, y + 65),
                fill=(245, 215, 155, 230),
            )

            draw.line(
                (x + 20, y + 90, x + 80, y + 90),
                fill=(235, 235, 255, 230),
                width=4,
            )

            draw.line(
                (x + 20, y + 108, x + 70, y + 108),
                fill=(235, 235, 255, 230),
                width=4,
            )


# ==================================================
# ILLUSTRATIONS
# ==================================================

def draw_illustration(draw, kind, cx, cy, size, t):
    pulse = 1 + 0.045 * math.sin(t * 2.5)
    radius = int(size * pulse)

    white = (250, 250, 255, 255)
    blue = (100, 185, 255, 255)
    purple = (195, 130, 255, 255)
    gold = (255, 210, 115, 255)

    if kind == "moon":
        draw.ellipse(
            (
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
            ),
            fill=gold,
        )

        draw.ellipse(
            (
                cx - radius // 3,
                cy - radius - 15,
                cx + radius + 30,
                cy + radius // 2,
            ),
            fill=(30, 25, 75, 255),
        )

        for i in range(8):
            x = int(cx + math.sin(t + i) * (radius + 100))
            y = int(cy + math.cos(t * 0.7 + i) * (radius + 100))

            draw.ellipse(
                (x - 3, y - 3, x + 3, y + 3),
                fill=white,
            )

    elif kind == "stairs":
        for i in range(5):
            x = cx - 160 + i * 65
            y = cy + 115 - i * 48

            draw.rectangle(
                (x, y, x + 70, cy + 150),
                fill=(
                    65 + i * 15,
                    90 + i * 15,
                    185 + i * 10,
                    255,
                ),
            )

        step = int((t * 1.2) % 5)
        px = int(cx - 130 + step * 65)
        py = int(cy + 85 - step * 48)

        draw.ellipse(
            (px - 13, py - 45, px + 13, py - 19),
            fill=white,
        )

        draw.line(
            (px, py - 19, px, py + 15),
            fill=purple,
            width=8,
        )

        draw.line(
            (px, py + 15, px - 15, py + 34),
            fill=white,
            width=7,
        )

        draw.line(
            (px, py + 15, px + 15, py + 34),
            fill=white,
            width=7,
        )

    elif kind == "book":
        lift = int(math.sin(t * 2) * 8)

        draw.rounded_rectangle(
            (
                cx - 145,
                cy - 95 + lift,
                cx,
                cy + 100 + lift,
            ),
            radius=12,
            fill=blue,
        )

        draw.rounded_rectangle(
            (
                cx,
                cy - 95 + lift,
                cx + 145,
                cy + 100 + lift,
            ),
            radius=12,
            fill=purple,
        )

        draw.line(
            (cx, cy - 95 + lift, cx, cy + 100 + lift),
            fill=white,
            width=5,
        )

        for i in range(4):
            y = cy - 45 + i * 38 + lift

            draw.line(
                (cx - 115, y, cx - 25, y),
                fill=white,
                width=3,
            )

            draw.line(
                (cx + 25, y, cx + 115, y),
                fill=white,
                width=3,
            )

    elif kind == "clock":
        draw.ellipse(
            (
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
            ),
            outline=white,
            width=8,
        )

        for i in range(12):
            angle = i * math.tau / 12

            x1 = int(cx + math.sin(angle) * (radius - 15))
            y1 = int(cy - math.cos(angle) * (radius - 15))

            x2 = int(cx + math.sin(angle) * (radius - 32))
            y2 = int(cy - math.cos(angle) * (radius - 32))

            draw.line(
                (x1, y1, x2, y2),
                fill=blue,
                width=4,
            )

        angle = t * 2.2

        draw.line(
            (
                cx,
                cy,
                int(cx + math.sin(angle) * radius * 0.65),
                int(cy - math.cos(angle) * radius * 0.65),
            ),
            fill=purple,
            width=8,
        )

        draw.ellipse(
            (cx - 8, cy - 8, cx + 8, cy + 8),
            fill=gold,
        )

    elif kind == "plant":
        ground = cy + 125
        sway = math.sin(t * 2) * 22

        growth = min(1.0, 0.35 + t / 5)

        tip_x = int(cx + sway)
        tip_y = int(ground - 185 * growth)

        draw.line(
            (cx, ground, tip_x, tip_y),
            fill=(100, 230, 160, 255),
            width=11,
        )

        for side in (-1, 1):
            leaf_x = tip_x + side * 55
            leaf_y = tip_y + 45

            draw.ellipse(
                (
                    leaf_x - 38,
                    leaf_y - 20,
                    leaf_x + 38,
                    leaf_y + 20,
                ),
                fill=(75, 215, 145, 255),
            )

        draw.ellipse(
            (cx - 120, ground - 5, cx + 120, ground + 24),
            fill=(145, 100, 80, 255),
        )

    elif kind == "waves":
        for row in range(6):
            y = cy - 110 + row * 43
            points = []

            for x in range(-10, WIDTH + 20, 10):
                yy = int(
                    y + math.sin(x * 0.018 + t * 2 + row) * 17
                )
                points.append((x, yy))

            draw.line(
                points,
                fill=(
                    55 + row * 17,
                    145 + row * 12,
                    245,
                    255,
                ),
                width=5,
            )

    elif kind == "rays":
        for i in range(14):
            angle = i * math.tau / 14 + t * 0.3

            x1 = int(cx + math.cos(angle) * (radius + 15))
            y1 = int(cy + math.sin(angle) * (radius + 15))

            x2 = int(cx + math.cos(angle) * (radius + 100))
            y2 = int(cy + math.sin(angle) * (radius + 100))

            draw.line(
                (x1, y1, x2, y2),
                fill=blue,
                width=5,
            )

        draw.ellipse(
            (cx - 60, cy - 60, cx + 60, cy + 60),
            fill=gold,
        )

    elif kind == "brain":
        for i in range(5):
            offset_x = (i - 2) * 43
            offset_y = int(math.sin(t * 2 + i) * 8)

            draw.ellipse(
                (
                    cx + offset_x - 38,
                    cy - 48 + offset_y,
                    cx + offset_x + 38,
                    cy + 48 + offset_y,
                ),
                fill=(175, 105 + i * 14, 220, 255),
                outline=white,
                width=3,
            )

        draw.line(
            (cx, cy - 40, cx, cy + 40),
            fill=white,
            width=4,
        )

    elif kind == "sun":
        for i in range(12):
            angle = i * math.tau / 12 + t * 0.2

            x1 = int(cx + math.cos(angle) * (radius + 15))
            y1 = int(cy + math.sin(angle) * (radius + 15))

            x2 = int(cx + math.cos(angle) * (radius + 65))
            y2 = int(cy + math.sin(angle) * (radius + 65))

            draw.line(
                (x1, y1, x2, y2),
                fill=gold,
                width=7,
            )

        draw.ellipse(
            (
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
            ),
            fill=gold,
        )

    elif kind == "fish":
        swim_x = int(math.sin(t * 1.5) * 35)

        fx = cx + swim_x
        fy = cy + int(math.sin(t * 2) * 12)

        draw.ellipse(
            (fx - 90, fy - 42, fx + 90, fy + 42),
            fill=(80, 190, 255, 255),
        )

        draw.polygon(
            [
                (fx - 85, fy),
                (fx - 135, fy - 35),
                (fx - 135, fy + 35),
            ],
            fill=purple,
        )

        draw.ellipse(
            (fx + 48, fy - 12, fx + 62, fy + 2),
            fill=(15, 25, 55, 255),
        )

        draw.arc(
            (fx - 35, fy - 28, fx + 35, fy + 28),
            start=270,
            end=90,
            fill=white,
            width=4,
        )

    elif kind == "memory":
        for i in range(4):
            offset = int(math.sin(t * 1.6 + i) * 10)
            x = cx - 135 + i * 90

            draw.rounded_rectangle(
                (
                    x,
                    cy - 90 + offset,
                    x + 75,
                    cy + 90 + offset,
                ),
                radius=12,
                fill=(
                    105 + i * 20,
                    95,
                    205,
                    255,
                ),
                outline=white,
                width=3,
            )

            draw.ellipse(
                (
                    x + 23,
                    cy - 60 + offset,
                    x + 52,
                    cy - 31 + offset,
                ),
                fill=gold,
            )

            draw.line(
                (
                    x + 15,
                    cy + 15 + offset,
                    x + 60,
                    cy + 15 + offset,
                ),
                fill=white,
                width=3,
            )

            draw.line(
                (
                    x + 15,
                    cy + 35 + offset,
                    x + 55,
                    cy + 35 + offset,
                ),
                fill=white,
                width=3,
            )


# ==================================================
# CAPTION TIMING
# ==================================================

def create_caption_timeline(text, duration):
    captions = split_captions(text, max_words=5)

    weights = [
        max(1, len(caption.split()))
        for caption in captions
    ]

    total_words = sum(weights)

    timeline = []
    current_time = 0.0

    for caption, weight in zip(captions, weights):
        segment_length = duration * weight / total_words

        timeline.append(
            (
                current_time,
                current_time + segment_length,
                caption,
            )
        )

        current_time += segment_length

    return timeline


def get_caption(t, timeline):
    for start, end, caption in timeline:
        if start <= t < end:
            return caption

    if timeline:
        return timeline[-1][2]

    return ""


# ==================================================
# VIDEO RENDERER
# ==================================================

def render_video(story, audio_path, video_path):
    audio = AudioFileClip(str(audio_path))
    duration = audio.duration

    if not duration or duration <= 0:
        audio.close()
        raise ValueError("Generated audio has no valid duration.")

    scenes = story["scenes"]

    scene_duration = duration / len(scenes)
    caption_timeline = create_caption_timeline(
        story["text"],
        duration,
    )

    # Pre-generate background particles.
    rng = random.Random(42)

    particles = [
        (
            rng.randrange(WIDTH),
            rng.randrange(HEIGHT),
            rng.randrange(2, 6),
            rng.uniform(8, 30),
        )
        for _ in range(35)
    ]

    def make_frame(t):
        scene_index = min(
            len(scenes) - 1,
            int(t / scene_duration),
        )

        scene = scenes[scene_index]

        scene_start = scene_index * scene_duration
        local_time = t - scene_start

        # Fade transitions near the beginning of each scene.
        fade_in = min(1.0, local_time / 0.35)

        # Generate the environment specific to this scene.
        background = make_background(scene["bg"], t)

        img = Image.fromarray(background).convert("RGBA")
        draw = ImageDraw.Draw(img, "RGBA")

        # Draw environment.
        draw_environment(
            draw,
            scene["bg"],
            local_time,
        )

        # Floating particles.
        for x, y0, radius, speed in particles:
            px = int(
                (x + math.sin(t * 0.6 + y0) * 18) % WIDTH
            )

            py = int(
                (y0 - t * speed) % HEIGHT
            )

            draw.ellipse(
                (
                    px - radius,
                    py - radius,
                    px + radius,
                    py + radius,
                ),
                fill=(190, 210, 255, 90),
            )

        # Scene number indicator.
        scene_number = f"SCENE {scene_index + 1:02d}"

        draw.rounded_rectangle(
            (38, 48, 205, 94),
            radius=18,
            fill=(5, 10, 30, 180),
            outline=(200, 215, 255, 150),
            width=2,
        )

        draw.text(
            (55, 60),
            scene_number,
            font=FONT_SMALL,
            fill=(225, 235, 255, 255),
        )

        # Animated headline.
        title_y = 150 + int(
            7 * math.sin(local_time * 2)
        )

        title_y = draw_centered(
            draw,
            scene["headline"],
            title_y,
            FONT_TITLE,
            (255, 255, 255, 255),
            max_width=640,
        )

        # Main illustration moves slightly.
        movement_x = int(
            math.sin(local_time * 1.2) * 14
        )

        movement_y = int(
            math.cos(local_time * 1.4) * 9
        )

        zoom = 1 + 0.035 * math.sin(local_time * 1.5)

        draw_illustration(
            draw,
            scene["kind"],
            WIDTH // 2 + movement_x,
            565 + movement_y,
            int(95 * zoom),
            local_time,
        )

        # Caption panel.
        caption = get_caption(
            t,
            caption_timeline,
        )

        panel_top = 865
        panel_bottom = 1095

        draw.rounded_rectangle(
            (
                32,
                panel_top,
                WIDTH - 32,
                panel_bottom,
            ),
            radius=25,
            fill=(4, 8, 25, 235),
            outline=(170, 190, 255, 210),
            width=2,
        )

        lines = wrap_text(
            draw,
            caption,
            FONT_CAPTION,
            WIDTH - 110,
        )

        line_height = FONT_CAPTION.size + 12

        text_y = (
            panel_top
            + (panel_bottom - panel_top - len(lines) * line_height) // 2
        )

        for line in lines:
            box = draw.textbbox(
                (0, 0),
                line,
                font=FONT_CAPTION,
            )

            text_x = (WIDTH - (box[2] - box[0])) // 2

            draw.text(
                (text_x + 2, text_y + 2),
                line,
                font=FONT_CAPTION,
                fill=(0, 0, 0, 255),
            )

            draw.text(
                (text_x, text_y),
                line,
                font=FONT_CAPTION,
                fill=(255, 255, 255, 255),
            )

            text_y += line_height

        # Video progress bar.
        bar_left = 40
        bar_right = WIDTH - 40
        bar_y = HEIGHT - 58

        draw.rounded_rectangle(
            (
                bar_left,
                bar_y,
                bar_right,
                bar_y + 8,
            ),
            radius=4,
            fill=(255, 255, 255, 75),
        )

        progress = max(
            0.0,
            min(1.0, t / duration),
        )

        progress_x = int(
            bar_left + (bar_right - bar_left) * progress
        )

        if progress_x > bar_left:
            draw.rounded_rectangle(
                (
                    bar_left,
                    bar_y,
                    progress_x,
                    bar_y + 8,
                ),
                radius=4,
                fill=(170, 205, 255, 255),
            )

        # Brief scene fade at the start.
        if fade_in < 1.0:
            overlay_alpha = int(
                255 * (1.0 - fade_in)
            )

            overlay = Image.new(
                "RGBA",
                (WIDTH, HEIGHT),
                (0, 0, 0, overlay_alpha),
            )

            img = Image.alpha_composite(
                img,
                overlay,
            )

        return np.asarray(
            img.convert("RGB")
        )

    video = None

    try:
        video = VideoClip(
            make_frame,
            duration=duration,
        )

        video = video.with_audio(audio)

        video.write_videofile(
            str(video_path),
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=2,
            logger="bar",
        )

    finally:
        if video is not None:
            video.close()

        audio.close()


# ==================================================
# AI VOICE GENERATION
# ==================================================

async def generate_voice(text, audio_path):
    communicator = edge_tts.Communicate(
        text=text,
        voice=VOICE,
    )

    await communicator.save(
        str(audio_path)
    )


# ==================================================
# MAIN AUTOMATION
# ==================================================

async def main():
    today = datetime.now().strftime("%Y-%m-%d")

    # One story is selected for each execution.
    story = random.choice(STORIES)

    safe_title = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        story["title"].lower(),
    ).strip("_")

    audio_path = (
        AUDIO_DIR
        / f"{today}_{safe_title}.mp3"
    )

    video_path = (
        VIDEO_DIR
        / f"{today}_{safe_title}.mp4"
    )

    script_path = (
        SCRIPT_DIR
        / f"script_{today}.json"
    )

    print("=" * 55)
    print("MEDIAFLOW V3 - STORY-DRIVEN ANIMATED SHORTS")
    print(f"Title: {story['title']}")
    print(f"Voice: {VOICE}")
    print(f"Scenes: {len(story['scenes'])}")
    print("=" * 55)

    script_path.write_text(
        json.dumps(
            story,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("\nStep 1: Generating narration...")

    await generate_voice(
        story["text"],
        audio_path,
    )

    print("\nStep 2: Rendering animated scenes...")

    render_video(
        story,
        audio_path,
        video_path,
    )

    print("\nSUCCESS")
    print(f"Audio: {audio_path}")
    print(f"Video: {video_path}")
    print(f"Script: {script_path}")


if __name__ == "__main__":
    asyncio.run(main())

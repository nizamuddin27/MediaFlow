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

# =========================================
# MEDIAFLOW V2 - ANIMATED SHORTS GENERATOR
# =========================================

WIDTH = 720
HEIGHT = 1280
FPS = 24
VOICE = "en-US-GuyNeural"

AUDIO_DIR = Path("output/audio")
VIDEO_DIR = Path("output/video")
SCRIPT_DIR = Path("output")

for folder in (AUDIO_DIR, VIDEO_DIR, SCRIPT_DIR):
    folder.mkdir(parents=True, exist_ok=True)

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
            ("A NEW DAY", "moon"),
            ("ONE SMALL STEP", "stairs"),
            ("KEEP LEARNING", "book"),
            ("TIME KEEPS MOVING", "clock"),
            ("PROGRESS TAKES TIME", "plant"),
            ("ONE STEP AT A TIME", "sun"),
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
            ("LIGHT MEETS WATER", "sun"),
            ("A WORLD OF BLUE", "waves"),
            ("COLORS OF LIGHT", "rays"),
            ("LIGHT TRAVELS DEEPER", "waves"),
            ("BLUE LIGHT RETURNS", "rays"),
            ("SCIENCE IS EVERYWHERE", "sun"),
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
            ("TIME TO REST", "moon"),
            ("YOUR BRAIN STAYS BUSY", "brain"),
            ("PROCESSING MEMORIES", "brain"),
            ("RECOVERY MATTERS", "plant"),
            ("RECHARGE YOURSELF", "sun"),
            ("REST IS PART OF THE WORK", "sun"),
        ],
    },
]


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


FONT_TITLE = load_font(43)
FONT_SUBTITLE = load_font(30)
FONT_SMALL = load_font(21)


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


def draw_centered(draw, text, y, font, fill, max_width=610):
    lines = wrap_text(draw, text, font, max_width)
    line_height = font.size + 12

    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        x = (WIDTH - (box[2] - box[0])) // 2

        draw.text(
            (x + 2, y + 3),
            line,
            font=font,
            fill=(0, 0, 0, 170),
        )
        draw.text((x, y), line, font=font, fill=fill)
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


def draw_illustration(draw, kind, cx, cy, size, t):
    """Draw original animated vector illustrations."""

    pulse = 1 + 0.06 * math.sin(t * 2.5)
    radius = int(size * pulse)

    white = (245, 247, 255, 255)
    blue = (100, 170, 255, 255)
    purple = (205, 130, 255, 255)

    if kind == "moon":
        draw.ellipse(
            (cx-radius, cy-radius, cx+radius, cy+radius),
            fill=(255, 220, 135, 255),
        )

        draw.ellipse(
            (
                cx-radius//3,
                cy-radius-15,
                cx+radius+30,
                cy+radius//2,
            ),
            fill=(19, 24, 58, 255),
        )

        for i in range(10):
            x = int(cx + math.sin(t+i) * (radius+100))
            y = int(cy + math.cos(t*0.7+i) * (radius+120))
            draw.ellipse((x-3, y-3, x+3, y+3), fill=white)

    elif kind == "stairs":
        for i in range(5):
            x = cx - 165 + i * 65
            y = cy + 120 - i * 50

            draw.rectangle(
                (x, y, x+70, cy+150),
                fill=(60+i*18, 90+i*15, 200, 255),
            )

        step = int((t * 1.3) % 5)
        px = int(cx - 130 + step * 65)
        py = int(cy + 90 - step * 50)

        draw.ellipse(
            (px-14, py-50, px+14, py-22),
            fill=white,
        )
        draw.line(
            (px, py-22, px, py+15),
            fill=purple,
            width=9,
        )
        draw.line(
            (px, py-8, px-18, py+8),
            fill=purple,
            width=7,
        )
        draw.line(
            (px, py-8, px+18, py+5),
            fill=purple,
            width=7,
        )
        draw.line(
            (px, py+15, px-15, py+35),
            fill=white,
            width=7,
        )
        draw.line(
            (px, py+15, px+15, py+35),
            fill=white,
            width=7,
        )

    elif kind == "book":
        draw.rounded_rectangle(
            (cx-150, cy-100, cx, cy+100),
            radius=12,
            fill=blue,
        )
        draw.rounded_rectangle(
            (cx, cy-100, cx+150, cy+100),
            radius=12,
            fill=purple,
        )
        draw.line(
            (cx, cy-100, cx, cy+100),
            fill=white,
            width=5,
        )

        for i in range(4):
            y = cy - 50 + i*40
            draw.line(
                (cx-120, y, cx-25, y),
                fill=white,
                width=3,
            )
            draw.line(
                (cx+25, y, cx+120, y),
                fill=white,
                width=3,
            )

        for i in range(3):
            x = int(cx + math.sin(t*1.7+i*2) * 190)
            y = int(cy + math.cos(t*1.7+i*2) * 130)

            draw.rounded_rectangle(
                (x-12, y-18, x+12, y+18),
                radius=4,
                fill=(220, 230, 255, 190),
            )

    elif kind == "clock":
        draw.ellipse(
            (cx-radius, cy-radius, cx+radius, cy+radius),
            outline=white,
            width=8,
        )

        for i in range(12):
            angle = i * math.tau / 12
            x1 = int(cx + math.sin(angle) * (radius-15))
            y1 = int(cy - math.cos(angle) * (radius-15))
            x2 = int(cx + math.sin(angle) * (radius-30))
            y2 = int(cy - math.cos(angle) * (radius-30))

            draw.line((x1, y1, x2, y2), fill=blue, width=4)

        angle = t * 2.5

        draw.line(
            (
                cx,
                cy,
                int(cx + math.sin(angle)*radius*0.65),
                int(cy - math.cos(angle)*radius*0.65),
            ),
            fill=purple,
            width=8,
        )

        draw.line(
            (
                cx,
                cy,
                int(cx + math.sin(angle*0.18)*radius*0.8),
                int(cy - math.cos(angle*0.18)*radius*0.8),
            ),
            fill=white,
            width=5,
        )

    elif kind == "plant":
        ground = cy + 125
        sway = math.sin(t*2) * 25
        growth = min(1.0, 0.25 + t/5)

        tip_x = int(cx + sway)
        tip_y = int(ground - 190*growth)

        draw.line(
            (cx, ground, tip_x, tip_y),
            fill=(100, 230, 160, 255),
            width=12,
        )

        for side in (-1, 1):
            leaf_x = tip_x + side*60
            leaf_y = tip_y + 45

            draw.ellipse(
                (
                    leaf_x-40,
                    leaf_y-20,
                    leaf_x+40,
                    leaf_y+20,
                ),
                fill=(75, 210, 145, 255),
            )

        draw.ellipse(
            (cx-125, ground-8, cx+125, ground+22),
            fill=(145, 105, 85, 255),
        )

    elif kind == "waves":
        for row in range(6):
            y = int(cy - 125 + row*48)
            points = []

            for x in range(-10, WIDTH+20, 10):
                yy = int(y + math.sin(x*0.018 + t*2 + row)*18)
                points.append((x, yy))

            draw.line(
                points,
                fill=(60+row*15, 140+row*12, 245, 255),
                width=6,
            )

    elif kind == "rays":
        for i in range(14):
            angle = i * math.tau / 14 + t*0.3

            x1 = int(cx + math.cos(angle)*(radius+15))
            y1 = int(cy + math.sin(angle)*(radius+15))
            x2 = int(cx + math.cos(angle)*(radius+95))
            y2 = int(cy + math.sin(angle)*(radius+95))

            draw.line(
                (x1, y1, x2, y2),
                fill=blue,
                width=5,
            )

        draw.ellipse(
            (cx-65, cy-65, cx+65, cy+65),
            fill=(255, 210, 100, 255),
        )

    elif kind == "brain":
        for i in range(5):
            offset_x = (i-2)*45
            offset_y = int(math.sin(t*2+i)*8)

            draw.ellipse(
                (
                    cx+offset_x-40,
                    cy-50+offset_y,
                    cx+offset_x+40,
                    cy+50+offset_y,
                ),
                fill=(180, 110+i*14, 220, 255),
                outline=white,
                width=3,
            )

        draw.line(
            (cx, cy-45, cx, cy+45),
            fill=white,
            width=4,
        )

    elif kind == "sun":
        for i in range(12):
            angle = i*math.tau/12 + t*0.2

            x1 = int(cx + math.cos(angle)*(radius+15))
            y1 = int(cy + math.sin(angle)*(radius+15))
            x2 = int(cx + math.cos(angle)*(radius+65))
            y2 = int(cy + math.sin(angle)*(radius+65))

            draw.line(
                (x1, y1, x2, y2),
                fill=(255, 210, 120, 255),
                width=7,
            )

        draw.ellipse(
            (cx-radius, cy-radius, cx+radius, cy+radius),
            fill=(255, 205, 90, 255),
        )


def render_video(story, audio_path, video_path):
    audio = AudioFileClip(str(audio_path))
    duration = audio.duration

    if not duration or duration <= 0:
        audio.close()
        raise ValueError("Generated audio has no valid duration.")

    captions = split_captions(story["text"])
    weights = [max(1, len(caption.split())) for caption in captions]
    total_words = sum(weights)

    caption_ranges = []
    current_time = 0.0

    for caption, weight in zip(captions, weights):
        length = duration * weight / total_words
        caption_ranges.append(
            (current_time, current_time + length, caption)
        )
        current_time += length

    scenes = story["scenes"]
    scene_duration = duration / len(scenes)

    y_gradient = np.linspace(
        0, 1, HEIGHT, dtype=np.float32
    )[:, None, None]

    top = np.array([9, 17, 47], dtype=np.float32)
    bottom = np.array([63, 20, 83], dtype=np.float32)

    background = np.repeat(
        top + (bottom-top)*y_gradient,
        WIDTH,
        axis=1,
    )
    background = np.clip(background, 0, 255).astype(np.uint8)

    rng = random.Random(42)
    particles = [
        (
            rng.randrange(WIDTH),
            rng.randrange(HEIGHT),
            rng.randrange(2, 7),
            rng.uniform(10, 35),
        )
        for _ in range(28)
    ]

    def make_frame(t):
        img = Image.fromarray(background).convert("RGBA")
        draw = ImageDraw.Draw(img, "RGBA")

        scene_index = min(
            len(scenes)-1,
            int(t / scene_duration),
        )

        headline, illustration = scenes[scene_index]
        local_time = t - scene_index*scene_duration

        for x, y0, r, speed in particles:
            px = int((x + math.sin(t*0.7+x)*20) % WIDTH)
            py = int((y0 - t*speed) % HEIGHT)

            draw.ellipse(
                (px-r, py-r, px+r, py+r),
                fill=(125, 170, 255, 95),
            )

        draw.rounded_rectangle(
            (40, 55, 290, 105),
            radius=20,
            fill=(255, 255, 255, 24),
            outline=(175, 190, 255, 170),
            width=2,
        )

        draw.text(
            (58, 67),
            "DID YOU KNOW?",
            font=FONT_SMALL,
            fill=(225, 230, 255, 255),
        )

        title_y = 165 + int(9*math.sin(local_time*2))

        draw_centered(
            draw,
            headline,
            title_y,
            FONT_TITLE,
            (255, 255, 255, 255),
        )

        zoom = 1 + 0.04*math.sin(local_time*1.3)

        draw_illustration(
            draw,
            illustration,
            WIDTH//2,
            565,
            int(105*zoom),
            local_time,
        )

        caption = captions[-1]

        for start, end, phrase in caption_ranges:
            if start <= t < end:
                caption = phrase
                break

        draw.rounded_rectangle(
            (35, 865, WIDTH-35, 1085),
            radius=26,
            fill=(5, 7, 24, 230),
            outline=(155, 175, 255, 180),
            width=2,
        )

        lines = wrap_text(
            draw,
            caption,
            FONT_SUBTITLE,
            WIDTH-110,
        )

        line_height = FONT_SUBTITLE.size + 12
        y_text = 975 - (len(lines)*line_height)//2

        for line in lines:
            box = draw.textbbox(
                (0, 0),
                line,
                font=FONT_SUBTITLE,
            )
            x_text = (WIDTH-(box[2]-box[0]))//2

            draw.text(
                (x_text, y_text),
                line,
                font=FONT_SUBTITLE,
                fill=(255, 255, 255, 255),
            )

            y_text += line_height

        left = 45
        right = WIDTH-45
        bar_y = HEIGHT-65

        draw.rounded_rectangle(
            (left, bar_y, right, bar_y+9),
            radius=5,
            fill=(255, 255, 255, 65),
        )

        progress = max(0, min(1, t/duration))
        end_x = int(left+(right-left)*progress)

        draw.rounded_rectangle(
            (left, bar_y, max(left+1, end_x), bar_y+9),
            radius=5,
            fill=(160, 190, 255, 255),
        )

        return np.asarray(img.convert("RGB"))

    video = None

    try:
        video = VideoClip(make_frame, duration=duration)
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


async def generate_voice(text, audio_path):
    communicator = edge_tts.Communicate(
        text=text,
        voice=VOICE,
    )
    await communicator.save(str(audio_path))


async def main():
    today = datetime.now().strftime("%Y-%m-%d")
    story = random.choice(STORIES)

    safe_title = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        story["title"].lower(),
    ).strip("_")

    audio_path = AUDIO_DIR / f"{today}_{safe_title}.mp3"
    video_path = VIDEO_DIR / f"{today}_{safe_title}.mp4"
    script_path = SCRIPT_DIR / f"script_{today}.json"

    print("="*45)
    print("MEDIAFLOW V2 - ANIMATED SHORTS")
    print(f"Title: {story['title']}")
    print(f"Voice: {VOICE}")
    print("="*45)

    script_path.write_text(
        json.dumps(story, indent=2),
        encoding="utf-8",
    )

    print("Step 1: Generating AI narration...")
    await generate_voice(story["text"], audio_path)

    print("Step 2: Rendering animated video...")
    render_video(story, audio_path, video_path)

    print("\nSUCCESS")
    print(f"Audio: {audio_path}")
    print(f"Video: {video_path}")


if __name__ == "__main__":
    asyncio.run(main())

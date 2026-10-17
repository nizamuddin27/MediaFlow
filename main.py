import asyncio
import math
import random
import re
from datetime import datetime
from pathlib import Path

import edge_tts
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import AudioFileClip, VideoClip


# ==========================================
# MEDIAFLOW V2 - ANIMATED FACELESS SHORTS
# ==========================================

W, H = 720, 1280
FPS = 24
VOICE = "en-US-GuyNeural"

AUDIO_DIR = Path("output/audio")
VIDEO_DIR = Path("output/video")
SCRIPT_DIR = Path("output")

for folder in (AUDIO_DIR, VIDEO_DIR, SCRIPT_DIR):
    folder.mkdir(parents=True, exist_ok=True)


# Six original visual scenes are generated for each video.
STORIES = [
    {
        "title": "The Power of Small Habits",
        "text": (
            "You do not need to change your entire life in one day. "
            "Start with one small habit. Read one page, walk for five "
            "minutes, or learn one new thing. Small actions may seem "
            "insignificant at first, but repeated consistently, "
            "they can create meaningful change. "
            "Progress is built one step at a time."
        ),
        "scenes": [
            ("NIGHT", "A NEW DAY", "moon"),
            ("START", "ONE SMALL STEP", "stairs"),
            ("LEARN", "KEEP LEARNING", "book"),
            ("TIME", "TIME KEEPS MOVING", "clock"),
            ("GROW", "PROGRESS TAKES TIME", "plant"),
            ("SUCCESS", "ONE STEP AT A TIME", "sun"),
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
            ("SUNLIGHT", "LIGHT MEETS WATER", "sun"),
            ("OCEAN", "A WORLD OF BLUE", "waves"),
            ("LIGHT", "COLORS OF LIGHT", "rays"),
            ("DEPTH", "LIGHT TRAVELS DEEPER", "waves"),
            ("DISCOVERY", "BLUE LIGHT RETURNS", "rays"),
            ("NATURE", "SCIENCE IS EVERYWHERE", "sun"),
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
            ("NIGHT", "TIME TO REST", "moon"),
            ("BRAIN", "YOUR BRAIN STAYS BUSY", "brain"),
            ("MEMORY", "PROCESSING MEMORIES", "brain"),
            ("REST", "RECOVERY MATTERS", "plant"),
            ("ENERGY", "RECHARGE YOURSELF", "sun"),
            ("HEALTH", "REST IS PART OF THE WORK", "sun"),
        ],
    },
]


def get_font(size, bold=True):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]

    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


FONT_BIG = get_font(48)
FONT_MED = get_font(32)
FONT_SMALL = get_font(22)


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    line = ""

    for word in words:
        trial = f"{line} {word}".strip()

        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word

    if line:
        lines.append(line)

    return lines


def draw_centered(draw, text, y, font, fill, max_width=620):
    lines = wrap_text(draw, text, font, max_width)
    line_height = font.size + 12

    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        x = (W - (box[2] - box[0])) // 2

        draw.text(
            (x + 2, y + 3),
            line,
            font=font,
            fill=(0, 0, 0, 150),
        )
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height

    return y


def make_captions(text):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    captions = []

    for sentence in sentences:
        words = sentence.split()

        # Keep subtitles short and readable.
        for i in range(0, len(words), 5):
            phrase = " ".join(words[i:i + 5])
            if phrase:
                captions.append(phrase)

    return captions


def draw_icon(draw, kind, cx, cy, size, t, scene_index):
    """Draw original vector-style animated illustrations."""

    pulse = 1 + 0.06 * math.sin(t * 3)
    r = int(size * pulse)

    blue = (112, 178, 255, 255)
    purple = (210, 139, 255, 255)
    white = (245, 247, 255, 255)

    if kind == "moon":
        draw.ellipse(
            (cx-r, cy-r, cx+r, cy+r),
            fill=(255, 219, 135, 255),
        )
        draw.ellipse(
            (cx-r//3, cy-r-10, cx+r+20, cy+r//2),
            fill=(25, 25, 65, 255),
        )

        for i in range(7):
            x = cx + int(math.sin(t+i)*180)
            y = cy + int(math.cos(t*0.8+i)*130)
            draw.ellipse((x-3, y-3, x+3, y+3), fill=white)

    elif kind == "stairs":
        for i in range(5):
            x = cx - 160 + i * 60
            y = cy + 110 - i * 55 + int(4 * math.sin(t*2+i))
            draw.rectangle(
                (x, y, x+65, cy+150),
                fill=(70+i*20, 100+i*18, 210, 255),
            )

        x = cx - 100 + int((t*35) % 220)
        y = cy - 25 - int((t*35) % 220) * 0.8

        draw.ellipse((x-15, y-15, x+15, y+15), fill=white)
        draw.line((x, y+15, x, y+65), fill=purple, width=9)
        draw.line((x, y+30, x-18, y+48), fill=purple, width=7)
        draw.line((x, y+30, x+18, y+45), fill=purple, width=7)

    elif kind == "book":
        left = (cx-145, cy-95, cx, cy+100)
        right = (cx, cy-95, cx+145, cy+100)

        draw.rounded_rectangle(left, radius=12, fill=blue)
        draw.rounded_rectangle(right, radius=12, fill=purple)
        draw.line((cx, cy-95, cx, cy+100), fill=white, width=5)

        for i in range(4):
            yy = cy - 45 + i*38
            draw.line((cx-115, yy, cx-25, yy), fill=white, width=3)
            draw.line((cx+25, yy, cx+115, yy), fill=white, width=3)

        angle = math.sin(t*2) * 12
        draw.arc(
            (cx-180, cy-130, cx+180, cy+130),
            start=int(180+angle),
            end=int(360+angle),
            fill=white,
            width=3,
        )

    elif kind == "clock":
        draw.ellipse(
            (cx-r, cy-r, cx+r, cy+r),
            outline=white,
            width=8,
        )

        for i in range(12):
            angle = i * math.tau / 12
            x1 = cx + math.sin(angle) * (r-15)
            y1 = cy - math.cos(angle) * (r-15)
            x2 = cx + math.sin(angle) * (r-28)
            y2 = cy - math.cos(angle) * (r-28)
            draw.line((x1, y1, x2, y2), fill=blue, width=4)

        angle = t * 2
        draw.line(
            (cx, cy, cx+math.sin(angle)*r*0.55,
             cy-math.cos(angle)*r*0.55),
            fill=purple,
            width=8,
        )
        draw.line(
            (cx, cy, cx+math.sin(angle*0.2)*r*0.8,
             cy-math.cos(angle*0.2)*r*0.8),
            fill=white,
            width=5,
        )

    elif kind == "plant":
        ground = cy + 130
        sway = math.sin(t*2) * 25
        grow = min(1.0, 0.25 + t/5)

        draw.line(
            (cx, ground, cx+sway, ground-190*grow),
            fill=(100, 230, 160, 255),
            width=12,
        )

        tip_x = cx+sway
        tip_y = ground-190*grow

        for side in (-1, 1):
            leaf_x = tip_x + side*65
            leaf_y = tip_y + 55
            draw.ellipse(
                (leaf_x-40, leaf_y-20, leaf_x+40, leaf_y+20),
                fill=(75, 210, 145, 255),
            )

        draw.ellipse(
            (cx-125, ground-8, cx+125, ground+22),
            fill=(150, 115, 90, 255),
        )

    elif kind == "waves":
        for row in range(5):
            y = cy - 100 + row*50

            points = []
            for x in range(-20, W+40, 10):
                yy = y + math.sin(x*0.018 + t*2 + row)*18
                points.append((x, yy))

            draw.line(
                points,
                fill=(65+row*18, 145+row*12, 245, 255),
                width=6,
            )

    elif kind == "rays":
        for i in range(12):
            angle = i * math.tau / 12 + t*0.25
            x = cx + math.cos(angle)*r
            y = cy + math.sin(angle)*r
            x2 = cx + math.cos(angle)*(r+100)
            y2 = cy + math.sin(angle)*(r+100)

            draw.line((x, y, x2, y2), fill=blue, width=5)

        draw.ellipse(
            (cx-65, cy-65, cx+65, cy+65),
            fill=(255, 220, 120, 255),
        )

    elif kind == "brain":
        for i in range(5):
            ox = (i-2)*45
            oy = math.sin(t*2+i)*8
            draw.ellipse(
                (cx+ox-40, cy-50+oy, cx+ox+40, cy+50+oy),
                fill=(190, 120+i*12, 220, 255),
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
            angle = i * math.tau / 12 + t*0.15
            x1 = cx + math.cos(angle)*(r+15)
            y1 = cy + math.sin(angle)*(r+15)
            x2 = cx + math.cos(angle)*(r+65)
            y2 = cy + math.sin(angle)*(r+65)

            draw.line(
                (x1, y1, x2, y2),
                fill=(255, 211, 120, 255),
                width=7,
            )

        draw.ellipse(
            (cx-r, cy-r, cx+r, cy+r),
            fill=(255, 204, 95, 255),
        )


def render_video(story, audio_path, video_path):
    audio = AudioFileClip(str(audio_path))
    duration = audio.duration

    captions = make_captions(story["text"])
    caption_weights = [max(1, len(c.split())) for c in captions]
    total_words = sum(caption_weights)

    caption_ranges = []
    now = 0.0

    for caption, weight in zip(captions, caption_weights):
        length = duration * weight / total_words
        caption_ranges.append((now, now + length, caption))
        now += length

    scene_duration = duration / len(story["scenes"])

    # Original generated gradient background.
    y = np.linspace(0, 1, H)[:, None, None]
    top = np.array([9, 17, 47], dtype=np.float32)
    bottom = np.array([63, 20, 83], dtype=np.float32)

    background = np.repeat(
        top + (bottom-top)*y,
        W,
        axis=1,
    )

    background = np.clip(background, 0, 255).astype(np.uint8)

    def make_frame(t):
        img = Image.fromarray(background.copy()).convert("RGBA")
        draw = ImageDraw.Draw(img, "RGBA")

        scene_index = min(
            len(story["scenes"])-1,
            int(t / scene_duration),
        )

        label, headline, icon = story["scenes"][scene_index]
        scene_t = t - scene_index * scene_duration

        # Camera-like zoom/pan effect on the main illustration.
        zoom = 1 + 0.035 * math.sin(scene_t * 1.2)
        icon_size = int(105 * zoom)

        # Floating particles move continuously.
        for i in range(22):
            px = (i*97 + int(t*24*(i%3+1))) % W
            py = (i*173 - int(t*35*(i%4+1))) % H
            radius = 2 + i % 5

            draw.ellipse(
                (px-radius, py-radius, px+radius, py+radius),
                fill=(120, 170, 255, 100),
            )

        # Scene label.
        draw.rounded_rectangle(
            (40, 55, 310, 110),
            radius=22,
            fill=(255, 255, 255, 25),
            outline=(170, 190, 255, 170),
            width=2,
        )

        draw.text(
            (60, 68),
            label,
            font=FONT_SMALL,
            fill=(220, 230, 255, 255),
        )

        # Moving scene headline.
        title_y = 175 + int(8 * math.sin(scene_t*2))
        draw_centered(
            draw,
            headline,
            title_y,
            FONT_BIG,
            (255, 255, 255, 255),
        )

        # Different animated illustration for each scene.
        draw_icon(
            draw,
            icon,
            W//2,
            575,
            icon_size,
            scene_t,
            scene_index,
        )

        # Current subtitle follows approximate narration timing.
        caption = captions[-1]

        for start, end, text in caption_ranges:
            if start <= t < end:
                caption = text
                break

        draw.rounded_rectangle(
            (35, 875, W-35, 1085),
            radius=26,
            fill=(5, 7, 24, 225),
            outline=(155, 175, 255, 180),
            width=2,
        )

        draw_centered(
            draw,
            caption,
            925,
            FONT_MED,
            (255, 255, 255, 255),
            max_width=590,
        )

        # Bottom progress indicator.
        left, right, py = 45, W-45, H-65

        draw.rounded_rectangle(
            (left, py, right, py+9),
            radius=5,
            fill=(255, 255, 255, 70),
        )

        progress = max(0, min(1, t/duration))
        end_x = int(left + (right-left)*progress)

        draw.rounded_rectangle(
            (left, py, max(left+1, end_x), py+9),
            radius=5,
            fill=(160, 190, 255, 255),
        )

        return np.asarray(img.convert("RGB"))

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

    video.close()
    audio.close()


async def generate_voice(text, path):
    tts = edge_tts.Communicate(
        text=text,
        voice=VOICE,
    )
    await tts.save(str(path))


async def main():
    today = datetime.now().strftime("%Y-%m-%d")

    # Choose one story per workflow run.
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
        __import__("json").dumps(story, indent=2),
        encoding="utf-8",
    )

    print("1/2 Generating AI voice...")
    await generate_voice(story["text"], audio_path)

    print("2/2 Rendering animated video...")
    render_video(story, audio_path, video_path)

    print("\nSUCCESS")
    print(f"Audio: {audio_path}")
    print(f"Video: {video_path}")


if __name__ == "__main__":
    asyncio.run(main())       threads=2,
        logger=None,
    )

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

    # Choose one script per run.
    script = random.choice(SCRIPTS)

    safe_title = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        script["title"].lower(),
    ).strip("_")

    audio_path = OUTPUT_AUDIO / f"{today}_{safe_title}.mp3"
    video_path = OUTPUT_VIDEO / f"{today}_{safe_title}.mp4"
    json_path = OUTPUT_SCRIPT / f"script_{today}.json"

    print("=" * 45)
    print("MEDIAFLOW - AI SHORTS GENERATOR")
    print(f"Title: {script['title']}")
    print(f"Voice: {VOICE}")
    print("=" * 45)

    json_path.write_text(
        json.dumps(script, indent=2),
        encoding="utf-8",
    )

    print("Generating AI narration...")
    await generate_voice(script["text"], audio_path)

    print("Generating original animated video...")
    build_video(script, audio_path, video_path)

    print("\nSUCCESS")
    print(f"Audio: {audio_path}")
    print(f"Video: {video_path}")


if __name__ == "__main__":
    asyncio.run(main())

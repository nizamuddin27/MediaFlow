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


# ==========================================
# MEDIAFLOW - FACELESS YOUTUBE SHORTS
# Original visuals + AI voice + subtitles
# ==========================================

WIDTH = 720
HEIGHT = 1280
FPS = 24

OUTPUT_AUDIO = Path("output/audio")
OUTPUT_VIDEO = Path("output/video")
OUTPUT_SCRIPT = Path("output")

VOICE = "en-US-GuyNeural"

OUTPUT_AUDIO.mkdir(parents=True, exist_ok=True)
OUTPUT_VIDEO.mkdir(parents=True, exist_ok=True)
OUTPUT_SCRIPT.mkdir(parents=True, exist_ok=True)


# Original scripts. Add more scripts here later.
SCRIPTS = [
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
    },
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
    },
    {
        "title": "Your Brain Needs Sleep",
        "text": (
            "Sleep is not simply a break from being awake. "
            "While you sleep, your brain processes information, "
            "supports memory, and helps your body recover. "
            "Consistently missing sleep can affect concentration "
            "and mood. So the next time you think sleep is wasted "
            "time, remember that rest is part of the work."
        ),
    },
]


def load_font(size, bold=False):
    """Load a font available on the GitHub Actions Ubuntu runner."""
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
            return ImageFont.truetype(path, size=size)

    return ImageFont.load_default()


def split_into_captions(text, max_words=6):
    """Split narration into short subtitle phrases."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks = []

    for sentence in sentences:
        words = sentence.split()

        for i in range(0, len(words), max_words):
            chunk = " ".join(words[i:i + max_words])
            if chunk:
                chunks.append(chunk)

    return chunks


def wrap_text(draw, text, font, max_width):
    """Wrap text so it fits within the screen."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        box = draw.textbbox((0, 0), test_line, font=font)

        if box[2] - box[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def make_gradient_background():
    """Create an original dark gradient background."""
    y = np.linspace(0, 1, HEIGHT)[:, None, None]

    top = np.array([13, 19, 48], dtype=np.float32)
    bottom = np.array([48, 17, 72], dtype=np.float32)

    gradient = top + (bottom - top) * y
    gradient = np.repeat(gradient, WIDTH, axis=1)

    return np.clip(gradient, 0, 255).astype(np.uint8)


def build_video(script, audio_path, video_path):
    """Render a vertical video with original animated graphics."""
    audio = AudioFileClip(str(audio_path))
    duration = audio.duration

    background = make_gradient_background()

    title_font = load_font(42, bold=True)
    subtitle_font = load_font(31, bold=True)
    small_font = load_font(20)

    title = script["title"]
    captions = split_into_captions(script["text"])

    # Estimate subtitle timing according to the number of words.
    weights = [max(1, len(caption.split())) for caption in captions]
    total_weight = sum(weights)

    caption_times = []
    current_time = 0.0

    for weight in weights:
        segment_duration = duration * weight / total_weight
        caption_times.append(
            (current_time, current_time + segment_duration)
        )
        current_time += segment_duration

    # Deterministic positions for decorative moving circles.
    rng = random.Random(42)
    particles = []

    for _ in range(24):
        particles.append({
            "x": rng.randint(20, WIDTH - 20),
            "y": rng.randint(0, HEIGHT),
            "radius": rng.randint(3, 12),
            "speed": rng.uniform(8, 28),
            "phase": rng.uniform(0, math.tau),
        })

    def render_frame(t):
        frame = background.copy()
        image = Image.fromarray(frame)
        draw = ImageDraw.Draw(image, "RGBA")

        # Floating circles create simple original animation.
        for particle in particles:
            x = particle["x"] + math.sin(
                t * 0.7 + particle["phase"]
            ) * 24

            y = (
                particle["y"] - t * particle["speed"]
            ) % HEIGHT

            r = particle["radius"]

            draw.ellipse(
                (x - r, y - r, x + r, y + r),
                fill=(120, 170, 255, 65),
            )

        # Top label.
        draw.rounded_rectangle(
            (42, 54, 265, 101),
            radius=18,
            fill=(255, 255, 255, 24),
            outline=(180, 190, 255, 100),
            width=2,
        )

        draw.text(
            (59, 66),
            "DID YOU KNOW?",
            font=small_font,
            fill=(220, 225, 255),
        )

        # Main title.
        title_lines = wrap_text(
            draw, title, title_font, WIDTH - 100
        )

        title_y = 220

        for line in title_lines:
            box = draw.textbbox((0, 0), line, font=title_font)
            line_width = box[2] - box[0]
            x = (WIDTH - line_width) // 2

            draw.text(
                (x + 2, title_y + 3),
                line,
                font=title_font,
                fill=(0, 0, 0, 100),
            )

            draw.text(
                (x, title_y),
                line,
                font=title_font,
                fill=(255, 255, 255),
            )

            title_y += 60

        # Decorative centre ring.
        center_x = WIDTH // 2
        center_y = 570

        pulse = 1 + 0.08 * math.sin(t * 2.0)
        radius = int(105 * pulse)

        draw.ellipse(
            (
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
            ),
            outline=(150, 180, 255, 150),
            width=4,
        )

        inner_radius = int(radius * 0.66)

        draw.ellipse(
            (
                center_x - inner_radius,
                center_y - inner_radius,
                center_x + inner_radius,
                center_y + inner_radius,
            ),
            outline=(230, 180, 255, 180),
            width=3,
        )

        # Select the current subtitle.
        caption = captions[-1]

        for index, (start, end) in enumerate(caption_times):
            if start <= t < end:
                caption = captions[index]
                break

        # Subtitle panel.
        panel_top = 850
        panel_bottom = 1050

        draw.rounded_rectangle(
            (35, panel_top, WIDTH - 35, panel_bottom),
            radius=28,
            fill=(5, 8, 25, 220),
            outline=(150, 170, 255, 160),
            width=2,
        )

        subtitle_lines = wrap_text(
            draw, caption, subtitle_font, WIDTH - 110
        )

        line_height = 44
        total_height = len(subtitle_lines) * line_height
        subtitle_y = (
            panel_top + (panel_bottom - panel_top - total_height) // 2
        )

        for line in subtitle_lines:
            box = draw.textbbox(
                (0, 0), line, font=subtitle_font
            )
            line_width = box[2] - box[0]
            x = (WIDTH - line_width) // 2

            draw.text(
                (x, subtitle_y),
                line,
                font=subtitle_font,
                fill=(255, 255, 255),
            )

            subtitle_y += line_height

        # Progress bar.
        bar_left = 45
        bar_right = WIDTH - 45
        bar_y = HEIGHT - 65

        draw.rounded_rectangle(
            (bar_left, bar_y, bar_right, bar_y + 10),
            radius=5,
            fill=(255, 255, 255, 55),
        )

        progress = min(1.0, max(0.0, t / duration))
        progress_right = int(
            bar_left + (bar_right - bar_left) * progress
        )

        draw.rounded_rectangle(
            (bar_left, bar_y, max(bar_left + 1, progress_right), bar_y + 10),
            radius=5,
            fill=(160, 190, 255, 255),
        )

        return np.asarray(image.convert("RGB"))

    video = VideoClip(render_frame, duration=duration)
    video = video.with_audio(audio)

    video.write_videofile(
        str(video_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=2,
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

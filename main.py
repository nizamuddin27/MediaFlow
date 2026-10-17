from datetime import datetime, timezone
from pathlib import Path
import random
import json

OUTPUT_DIR = Path("output")

FACTS = [
    {
        "title": "Why Your Brain Loves Sleep",
        "script": (
            "Did you know your brain stays busy while you sleep? "
            "During sleep, your brain processes information and helps "
            "form memories. Sleep is not wasted time. It is part of "
            "how your brain learns and recovers. So tonight, give your "
            "brain the rest it deserves."
        )
    },
    {
        "title": "The Power of Small Habits",
        "script": (
            "You do not need to change your whole life in one day. "
            "Small habits can build meaningful progress over time. "
            "Read one page, learn one new thing, or take one small step. "
            "Consistency matters more than a perfect start. "
            "Start small, and keep moving forward."
        )
    },
    {
        "title": "Why the Ocean Looks Blue",
        "script": (
            "Have you ever wondered why the ocean often looks blue? "
            "Water absorbs longer wavelengths of visible light more "
            "strongly than blue wavelengths. The light that reaches "
            "your eyes depends on depth, particles, and lighting. "
            "The ocean's colour is more fascinating than it first appears."
        )
    }
]

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    selected = random.choice(FACTS)

    video_data = {
        "date": today,
        "title": selected["title"],
        "script": selected["script"],
        "status": "script_generated"
    }

    output_file = OUTPUT_DIR / f"script_{today}.json"
    output_file.write_text(
        json.dumps(video_data, indent=2),
        encoding="utf-8"
    )

    print("=" * 40)
    print("MEDIAFLOW - SCRIPT GENERATOR")
    print("=" * 40)
    print(f"Title: {selected['title']}")
    print(f"Script: {selected['script']}")
    print(f"Saved to: {output_file}")
    print("Status: Script generated successfully.")
    print("=" * 40)

if __name__ == "__main__":
    main()

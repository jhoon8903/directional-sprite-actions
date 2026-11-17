"""Draft a three-phase recoil from registered idle frames without model inference."""
import argparse
import io
import json
from pathlib import Path

from PIL import Image

# Screen-space motion away from an impact arriving from the facing direction.
BACK = {
    "S": (0, -1), "SW": (1, -1), "W": (1, 0), "NW": (1, 1),
    "N": (0, 1), "NE": (-1, 1), "E": (-1, 0), "SE": (-1, -1),
}


def render(project, distance):
    character = json.loads((project / "character.json").read_text())
    actions = json.loads((project / "actions.json").read_text())
    if [frame[0] for frame in actions["hit"]["frames"]] != ["impact", "recoil", "settle"]:
        raise ValueError("This generator expects the impact/recoil/settle hit preset.")
    size = character["size"]
    directions = character["directions"]
    sheet = Image.new("RGBA", (3 * size, len(directions) * size))
    for row, direction in enumerate(directions):
        if direction not in BACK:
            raise ValueError(f"Unknown screen direction {direction}")
        source = project / "frames" / "idle" / direction / "stand.png"
        with Image.open(source) as image:
            if image.mode != "RGBA" or image.size != (size, size):
                raise ValueError(f"Expected {size}x{size} RGBA at {source}")
            bounds = image.getchannel("A").getbbox()
            if bounds is None:
                raise ValueError(f"Empty pose at {source}")
            sprite = image.crop(bounds)
        left, top, right, bottom = bounds
        dx, dy = BACK[direction]
        for col, step in enumerate([0, distance, 0]):
            pose = sprite
            x, y = left + dx * step, top + dy * step
            if col == 0:
                # Squash toward the original foot line on contact.
                height = max(1, sprite.height - distance)
                pose = sprite.resize((sprite.width, height), Image.Resampling.NEAREST)
                y = bottom - height
            if x < 0 or y < 0 or x + pose.width > size or y + pose.height > size:
                raise ValueError(f"{direction} clips at recoil {distance}px. Increase shared margins or reduce --distance.")
            sheet.alpha_composite(pose, (col * size + x, row * size + y))
    return sheet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--distance", default=2, type=int)
    args = parser.parse_args()
    if args.distance < 1:
        parser.error("--distance must be a positive pixel count")
    try:
        sheet = render(args.project, args.distance)
        encoded = io.BytesIO()
        sheet.save(encoded, format="PNG")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as output:
            output.write(encoded.getvalue())
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"draft-hit: {error}\n")


if __name__ == "__main__":
    main()

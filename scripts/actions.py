#!/usr/bin/env python3
"""Assemble validated directional animation frames into portable sprite sheets.

The project folder deliberately contains only approved source frames and generated
outputs; this tool does not touch an engine project.  A frame name may be shared
between actions with ``@action`` (loads ``frames/action/DIR/action.png``) or
``@action/name`` (loads ``frames/action/DIR/name.png``).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import os
from tempfile import NamedTemporaryFile
from pathlib import Path
from typing import Any, Iterable, Tuple

from PIL import Image


DIRECTIONS = ("S", "SW", "W", "NW", "N", "NE", "E", "SE")
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
SCRIPT_ROOT = Path(__file__).resolve().parent.parent
PRESETS = SCRIPT_ROOT / "assets" / "actions.json"


class ActionError(Exception):
    pass


def fail(message: str) -> None:
    raise ActionError(message)


def read_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        fail(f"Missing required file: {path}")
    except json.JSONDecodeError as error:
        fail(f"Invalid JSON in {path}: {error}")


def require_identifier(value: str, label: str) -> str:
    if not IDENTIFIER.fullmatch(value):
        fail(f"{label} must use only letters, digits, underscores, and hyphens: {value!r}")
    return value


def project_config(project: Path) -> Tuple[int, Tuple[str, ...], dict[str, Any]]:
    character = read_json(project / "character.json")
    size = character.get("size")
    directions = character.get("directions")
    if not isinstance(size, int) or size <= 0:
        fail("character.json must contain a positive integer 'size'")
    if not isinstance(directions, list) or not directions or not all(isinstance(item, str) for item in directions):
        fail("character.json must contain a string array 'directions'")
    if len(set(directions)) != len(directions) or any(item not in DIRECTIONS for item in directions):
        fail("character.json directions must be a non-empty, duplicate-free subset of S, SW, W, NW, N, NE, E, SE")
    return size, tuple(directions), character


def catalog(project: Path) -> dict[str, Any]:
    actions = read_json(project / "actions.json")
    if not isinstance(actions, dict):
        fail("actions.json must contain an object keyed by action ID")
    for path in sorted((project / "actions").glob("*.json")):
        name = require_identifier(path.stem, "Action")
        if name in actions:
            fail(f"Duplicate action '{name}' in actions.json and {path}")
        actions[name] = read_json(path)
    return actions


def action_spec(project: Path, action: str) -> dict[str, Any]:
    require_identifier(action, "Action")
    spec = catalog(project).get(action)
    if not isinstance(spec, dict):
        fail(f"Unknown or invalid action '{action}'. See the list and add commands.")
    frames = spec.get("frames")
    if not isinstance(spec.get("loop"), bool) or not isinstance(frames, list) or not frames:
        fail(f"Action '{action}' must provide boolean loop and a non-empty frames list")
    for index, frame in enumerate(frames):
        if (not isinstance(frame, list) or len(frame) != 2 or not isinstance(frame[0], str)
                or not frame[0] or not isinstance(frame[1], int) or frame[1] <= 0):
            fail(f"Action '{action}' frame {index} must be [name, positive_duration_ms]")
        validate_frame_name(frame[0], f"Action '{action}' frame {index} name")
    return spec


def validate_frame_name(name: str, label: str) -> None:
    if name.startswith("@"):
        reference = name[1:]
        action, separator, frame = reference.partition("/")
        require_identifier(action, label)
        if separator:
            require_identifier(frame, label)
    else:
        require_identifier(name, label)


def source_path(project: Path, action: str, direction: str, name: str) -> Path:
    require_identifier(action, "Action")
    if direction not in DIRECTIONS:
        fail(f"Invalid direction: {direction!r}")
    validate_frame_name(name, "Frame name")
    if not name.startswith("@"):
        return project / "frames" / action / direction / f"{name}.png"
    reference = name[1:]
    if not reference:
        fail(f"Action '{action}' has an empty shared-frame reference")
    source_action, separator, source_name = reference.partition("/")
    if not source_action:
        fail(f"Invalid shared-frame reference '{name}'")
    return project / "frames" / source_action / direction / f"{source_name or source_action}.png"


def validate_image(path: Path, size: int) -> Image.Image:
    if not path.is_file():
        fail(f"Missing approved frame: {path}")
    try:
        with Image.open(path) as opened:
            if opened.mode != "RGBA":
                fail(f"Frame must be RGBA (not {opened.mode}): {path}")
            if opened.size != (size, size):
                fail(f"Frame must be {size}x{size} (not {opened.width}x{opened.height}): {path}")
            image = opened.copy()
    except OSError as error:
        fail(f"Unreadable PNG {path}: {error}")
    if image.getchannel("A").getbbox() is None:
        fail(f"Frame has no visible (alpha > 0) pixels: {path}")
    return image


def iter_expected(project: Path, action: str) -> Iterable[Tuple[str, str, int, Path]]:
    _, directions, _ = project_config(project)
    spec = action_spec(project, action)
    for direction in directions:
        for index, (name, duration) in enumerate(spec["frames"]):
            yield direction, name, duration, source_path(project, action, direction, name)


def command_init(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    require_identifier(args.motion, "Motion profile")
    if args.size <= 0:
        fail("--size must be a positive integer")
    if not PRESETS.is_file():
        fail(f"Bundled action presets are unavailable: {PRESETS}")
    existing = [path for path in (project / "actions.json", project / "character.json") if path.exists()]
    if existing:
        fail("Refusing to overwrite existing project configuration: " + ", ".join(map(str, existing)))
    project.mkdir(parents=True, exist_ok=True)
    base = read_json(PRESETS)
    motions = read_json(SCRIPT_ROOT / "assets" / "motions.json")
    profile = motions.get(args.motion, {})
    if args.motion == "biped":
        actions = base
    else:
        actions = {"idle": base["idle"], "hit": base["hit"], **profile.get("actions", {})}
    character = {"size": args.size, "directions": list(DIRECTIONS), "motion": args.motion,
                 "anchor": args.anchor or profile.get("anchor", "ground")}
    (project / "actions.json").write_text(json.dumps(actions, indent=2) + "\n", encoding="utf-8")
    (project / "character.json").write_text(json.dumps(character, indent=2) + "\n", encoding="utf-8")
    print(f"Initialized {project}")


def command_list(args: argparse.Namespace) -> None:
    for action in catalog(Path(args.project)):
        print(action)


def command_add(args: argparse.Namespace) -> None:
    project = Path(args.project)
    action = require_identifier(args.action, "Action")
    actions = catalog(project)
    frames = []
    for token in args.frames:
        name, separator, duration = token.rpartition(":")
        if not separator or not duration.isascii() or not duration.isdigit() or int(duration) <= 0:
            fail(f"Expected POSE:POSITIVE_MILLISECONDS, got {token!r}")
        validate_frame_name(name, "Pose")
        frames.append([name, int(duration)])
    spec = {"loop": args.loop, "frames": frames}
    if action in actions:
        if actions[action] == spec:
            print(f"Already registered: {action}")
            return
        fail(f"Action '{action}' already has a different definition")
    folder = project / "actions"
    folder.mkdir(exist_ok=True)
    # Publish the completed definition without replacing a concurrent addition.
    path = folder / f"{action}.json"
    with NamedTemporaryFile(dir=folder, delete=False) as temp:
        temp_path = Path(temp.name)
    try:
        temp_path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
        try:
            os.link(temp_path, path)
        except FileExistsError:
            if read_json(path) != spec:
                fail(f"Conflicting definition at {path}")
    finally:
        temp_path.unlink(missing_ok=True)
    print(f"Registered {action} at {path}")


def command_plan(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    _, directions, _ = project_config(project)
    expected = list(iter_expected(project, args.action))
    missing = [(direction, name, path) for direction, name, _, path in expected if not path.is_file()]
    print(f"action={args.action} directions={len(directions)} frames_per_direction={len(expected) // len(directions)} expected={len(expected)}")
    if missing:
        print(f"missing={len(missing)}")
        for direction, name, path in missing:
            print(f"  {direction}/{name}: {path}")
    else:
        print("missing=0 (all required source paths exist; build will still validate PNG mode, size, and alpha)")


def command_build(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    size, directions, _ = project_config(project)
    spec = action_spec(project, args.action)
    frames = spec["frames"]
    if args.direction and args.direction not in directions:
        fail(f"--direction must be configured in character.json: {args.direction}")
    build_directions = (args.direction,) if args.direction else directions
    sheet = Image.new("RGBA", (size * len(frames), size * len(build_directions)), (0, 0, 0, 0))
    direction_frames: list[list[Image.Image]] = []
    for y, direction in enumerate(build_directions):
        row: list[Image.Image] = []
        for x, (name, duration) in enumerate(frames):
            image = validate_image(source_path(project, args.action, direction, name), size)
            sheet.alpha_composite(image, (x * size, y * size))
            row.append(image)
        direction_frames.append(row)
    if args.direction:
        # Direction builds make one directional set reviewable before every pose is supplied.
        output = project / "build" / args.action / "directions" / args.direction
    else:
        output = project / "build" / args.action
    output.mkdir(parents=True, exist_ok=True)
    sheet.save(output / "sheet.png")
    # Each GIF time step is an opaque, all-direction contact row, avoiding palette
    # transparency ambiguity while retaining the authored pose timing.
    preview_images: list[Image.Image] = []
    for frame_index in range(len(frames)):
        preview = Image.new("RGB", (size * len(build_directions), size), (0, 0, 0))
        for direction_index in range(len(build_directions)):
            preview.paste(direction_frames[direction_index][frame_index], (direction_index * size, 0),
                         direction_frames[direction_index][frame_index])
        preview_images.append(preview)
    gif_args: dict[str, Any] = {"save_all": True, "append_images": preview_images[1:],
                                "duration": [duration for _, duration in frames], "disposal": 2}
    if spec["loop"]:
        gif_args["loop"] = 0
    preview_images[0].save(output / "preview.gif", **gif_args)
    clip = {
        "action": args.action,
        "loop": spec["loop"],
        "size": size,
        "directions": list(build_directions),
        "grid": {"columns": len(frames), "rows": len(build_directions), "order": "row=direction,column=frame"},
        "frames": [{"name": name, "duration_ms": duration} for name, duration in frames],
        "rects": {direction: [
            {"name": name, "duration_ms": duration,
             "rect": {"x": index * size, "y": row * size, "width": size, "height": size}}
            for index, (name, duration) in enumerate(frames)]
            for row, direction in enumerate(build_directions)},
        "preview": {"direction_order": list(build_directions), "layout": "one horizontal row per timestep",
                    "opaque_background": "#000000", "loop": spec["loop"]},
    }
    (output / "clip.json").write_text(json.dumps(clip, indent=2) + "\n", encoding="utf-8")
    print(f"Built {output}")


def command_import_sheet(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    size, directions, _ = project_config(project)
    spec = action_spec(project, args.action)
    source = Path(args.png).resolve()
    if not source.is_file():
        fail(f"Missing source sheet: {source}")
    try:
        with Image.open(source) as opened:
            if opened.mode != "RGBA":
                fail(f"Sheet must be RGBA (not {opened.mode}): {source}")
            expected_size = (size * len(spec["frames"]), size * len(directions))
            if opened.size != expected_size:
                fail(f"Sheet must be {expected_size[0]}x{expected_size[1]} (not {opened.width}x{opened.height}): {source}")
            image = opened.copy()
    except OSError as error:
        fail(f"Unreadable PNG {source}: {error}")
    tiles: dict[Path, Image.Image] = {}
    for direction in directions:
        for x, (name, _) in enumerate(spec["frames"]):
            if name.startswith("@"):
                fail("import-sheet cannot write shared (@...) frames; import their owning action instead")
            y = directions.index(direction)
            tile = image.crop((x * size, y * size, (x + 1) * size, (y + 1) * size))
            if tile.getchannel("A").getbbox() is None:
                fail(f"Imported tile has no visible pixels: {direction}/{name}")
            destination = project / "frames" / args.action / direction / f"{name}.png"
            if destination in tiles and tiles[destination].tobytes() != tile.tobytes():
                fail(f"Repeated pose has differing cells: {direction}/{name}")
            tiles[destination] = tile
    # Prevalidate the complete transaction. Exact existing tiles make retries safe;
    # any different approved frame aborts before a new file is written.
    to_write: list[Tuple[Path, Image.Image]] = []
    for destination, tile in tiles.items():
        if destination.exists():
            existing = validate_image(destination, size)
            if existing.tobytes() != tile.tobytes():
                fail(f"Refusing to overwrite conflicting approved frame: {destination}")
        else:
            to_write.append((destination, tile))
    for destination, tile in to_write:
        destination.parent.mkdir(parents=True, exist_ok=True)
        tile.save(destination)
    print(f"Imported {len(to_write)} new frames ({len(tiles) - len(to_write)} already compatible) into {project / 'frames' / args.action}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="create a project configuration from bundled presets")
    init.add_argument("project")
    init.add_argument("--size", type=int, default=64)
    init.add_argument("--motion", default="biped", help="movement profile or custom ID; see assets/motions.json")
    init.add_argument("--anchor", choices=["ground", "center"], help="anchor for procedural hit squash")
    init.set_defaults(func=command_init)
    listing = commands.add_parser("list", help="list actions registered for this character")
    listing.add_argument("project")
    listing.set_defaults(func=command_list)
    add = commands.add_parser("add", help="register a project action with ordered poses and timings")
    add.add_argument("project")
    add.add_argument("action")
    add.add_argument("frames", nargs="+", metavar="POSE:MS")
    add.add_argument("--loop", action="store_true", help="repeat the clip (default: play once)")
    add.set_defaults(func=command_add)
    for name, function, help_text in (("plan", command_plan, "list required source frames"),
                                      ("build", command_build, "assemble validated sources"),
                                      ("import-sheet", command_import_sheet, "split a normalized RGBA source sheet")):
        item = commands.add_parser(name, help=help_text)
        item.add_argument("project")
        item.add_argument("action")
        if name == "build":
            item.add_argument("--direction", choices=DIRECTIONS,
                              help="build a single configured direction into build/ACTION/directions/DIR")
        if name == "import-sheet":
            item.add_argument("png")
        item.set_defaults(func=function)
    return result


def main() -> int:
    try:
        args = parser().parse_args()
        args.func(args)
        return 0
    except ActionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

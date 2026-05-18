#!/usr/bin/env python3
import argparse
import shlex
from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def find_images(image_dir: Path) -> list[Path]:
    if not image_dir.is_dir():
        raise SystemExit(f"Image directory not found: {image_dir}")

    images = sorted(
        path
        for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not images:
        extensions = ", ".join(sorted(IMAGE_EXTENSIONS))
        raise SystemExit(f"No supported images found in {image_dir}; expected: {extensions}")

    return images


def command_for(image_path: Path) -> str:
    image_arg = shlex.quote(f"../images/{image_path.name}")
    return (
        "("
        "cd results && "
        f"python3 ../single-image-process.py {image_arg}"
        ") &"
    )


def build_script(images: list[Path], max_jobs: int) -> str:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "mkdir -p results",
        "",
    ]

    for index, image_path in enumerate(images, start=1):
        lines.append(command_for(image_path))
        if index % max_jobs == 0:
            lines.extend(["wait", ""])

    if len(images) % max_jobs:
        lines.append("wait")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate batch_run.sh for image processing.")
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=4,
        help="Number of images to run in parallel in each generated batch. Default: 4.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.max_jobs < 1:
        raise SystemExit("--max-jobs must be at least 1")

    root = Path(__file__).resolve().parent
    image_dir = root / "images"
    script_path = root / "batch_run.sh"

    images = find_images(image_dir)
    script_path.write_text(build_script(images, args.max_jobs), encoding="utf-8")
    script_path.chmod(script_path.stat().st_mode | 0o755)

    print(f"Wrote {script_path} with {len(images)} image command(s), {args.max_jobs} at a time.")
    print("Run it with: bash batch_run.sh")
    print("Change concurrency by regenerating it, e.g. python3 generate_batch_run.py --max-jobs 8")


if __name__ == "__main__":
    main()

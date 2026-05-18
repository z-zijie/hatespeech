#!/usr/bin/env python3
import argparse
import re
import shlex
from dataclasses import dataclass
from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
SAFE_STEM_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")


@dataclass(frozen=True)
class BatchImage:
    path: Path
    label: str
    output_stem: str


def find_images(image_dir: Path) -> list[Path]:
    if not image_dir.is_dir():
        raise SystemExit(f"Image directory not found: {image_dir}")

    images = sorted(
        path.resolve()
        for path in image_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not images:
        extensions = ", ".join(sorted(IMAGE_EXTENSIONS))
        raise SystemExit(f"No supported images found in {image_dir}; expected: {extensions}")

    return images


def safe_stem(label: str) -> str:
    stem = str(Path(label).with_suffix(""))
    stem = stem.replace("/", "__")
    stem = SAFE_STEM_PATTERN.sub("_", stem)
    return stem.strip("._") or "image"


def batch_images_for(image_dir: Path) -> list[BatchImage]:
    seen_stems: dict[str, int] = {}
    batch_images = []

    for image_path in find_images(image_dir):
        label = image_path.relative_to(image_dir).as_posix()
        base_stem = safe_stem(label)
        count = seen_stems.get(base_stem, 0) + 1
        seen_stems[base_stem] = count
        output_stem = base_stem if count == 1 else f"{base_stem}__{count}"
        batch_images.append(BatchImage(path=image_path, label=label, output_stem=output_stem))

    return batch_images


def command_for(batch_image: BatchImage) -> str:
    image_arg = shlex.quote(str(batch_image.path))
    result_stem_arg = shlex.quote(batch_image.output_stem)
    image_label_arg = shlex.quote(batch_image.label)
    log_arg = shlex.quote(f"../logs/{batch_image.output_stem}.log")
    return (
        "("
        "cd results && "
        f"python3 ../single-image-process.py --result-stem {result_stem_arg} --image-label {image_label_arg} {image_arg} > {log_arg} 2>&1"
        ") &"
    )


def progress_helpers(total_images: int) -> list[str]:
    return [
        f"TOTAL_IMAGES={total_images}",
        "completed=0",
        "bar_width=20",
        "",
        "print_progress() {",
        "    local percent=0",
        "    local filled=0",
        "    local empty=0",
        "    local bar=\"\"",
        "",
        "    if [ \"$TOTAL_IMAGES\" -gt 0 ]; then",
        "        percent=$((completed * 100 / TOTAL_IMAGES))",
        "        filled=$((completed * bar_width / TOTAL_IMAGES))",
        "    fi",
        "    empty=$((bar_width - filled))",
        "    bar=\"$(printf '%*s' \"$filled\" '' | tr ' ' '#')\"",
        "    bar=\"${bar}$(printf '%*s' \"$empty\" '' | tr ' ' '-')\"",
        "",
        "    printf '[progress] [%s] %d/%d %d%%\\n' \"$bar\" \"$completed\" \"$TOTAL_IMAGES\" \"$percent\"",
        "}",
        "",
        "wait_and_print() {",
        "    local batch_count=\"$1\"",
        "",
        "    wait",
        "",
        "    completed=$((completed + batch_count))",
        "    print_progress",
        "}",
        "",
    ]


def build_script(images: list[BatchImage], max_jobs: int) -> str:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "mkdir -p results logs",
        "",
        *progress_helpers(len(images)),
        "print_progress",
    ]

    batch_count = 0
    for index, batch_image in enumerate(images, start=1):
        lines.append(command_for(batch_image))
        batch_count += 1
        if index % max_jobs == 0:
            lines.extend([f"wait_and_print {batch_count}", ""])
            batch_count = 0

    if batch_count:
        lines.append(f"wait_and_print {batch_count}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate batch_run.sh for image processing.")
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=4,
        help="Number of images to run in parallel in each generated batch. Default: 4.",
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=Path("images"),
        help="Directory to scan recursively for input images. Default: images.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.max_jobs < 1:
        raise SystemExit("--max-jobs must be at least 1")

    root = Path(__file__).resolve().parent
    image_dir = args.image_dir.expanduser()
    if not image_dir.is_absolute():
        image_dir = root / image_dir
    image_dir = image_dir.resolve()
    script_path = root / "batch_run.sh"

    images = batch_images_for(image_dir)
    script_path.write_text(build_script(images, args.max_jobs), encoding="utf-8")
    script_path.chmod(script_path.stat().st_mode | 0o755)

    print(f"Wrote {script_path} with {len(images)} recursive image command(s), {args.max_jobs} at a time.")
    print(f"Input directory: {image_dir}")
    print("Run it with: bash batch_run.sh")
    print("Change concurrency by regenerating it, e.g. python3 generate_batch_run.py --max-jobs 8")


if __name__ == "__main__":
    main()

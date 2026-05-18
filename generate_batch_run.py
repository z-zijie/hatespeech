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
    log_arg = shlex.quote(f"../logs/{image_path.stem}.log")
    return (
        "("
        "cd results && "
        f"python3 ../single-image-process.py {image_arg} > {log_arg} 2>&1"
        ") &"
    )


def progress_helpers(total_images: int) -> list[str]:
    return [
        f"TOTAL_IMAGES={total_images}",
        "completed=0",
        "failed=0",
        "overall_status=0",
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
        "    if [ \"$failed\" -gt 0 ]; then",
        "        printf '[progress] [%s] %d/%d %d%% (%d failed)\\n' \"$bar\" \"$completed\" \"$TOTAL_IMAGES\" \"$percent\" \"$failed\"",
        "    else",
        "        printf '[progress] [%s] %d/%d %d%%\\n' \"$bar\" \"$completed\" \"$TOTAL_IMAGES\" \"$percent\"",
        "    fi",
        "}",
        "",
        "wait_for_batch() {",
        "    local pid",
        "    local status",
        "",
        "    for pid in \"$@\"; do",
        "        if wait \"$pid\"; then",
        "            status=0",
        "        else",
        "            status=$?",
        "            failed=$((failed + 1))",
        "            overall_status=1",
        "            printf '[progress] job failed pid=%s exit=%d\\n' \"$pid\" \"$status\"",
        "        fi",
        "",
        "        completed=$((completed + 1))",
        "        print_progress",
        "    done",
        "}",
        "",
    ]


def build_script(images: list[Path], max_jobs: int) -> str:
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "mkdir -p results logs",
        "",
        *progress_helpers(len(images)),
        "print_progress",
        "",
        "batch_pids=()",
    ]

    for index, image_path in enumerate(images, start=1):
        lines.append(command_for(image_path))
        lines.append("batch_pids+=(\"$!\")")
        if index % max_jobs == 0:
            lines.extend(["wait_for_batch \"${batch_pids[@]}\"", "batch_pids=()", ""])

    if len(images) % max_jobs:
        lines.append("wait_for_batch \"${batch_pids[@]}\"")
    lines.extend(["", "exit \"$overall_status\""])
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

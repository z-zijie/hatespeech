#!/usr/bin/env python3
import argparse
import base64
import json
import mimetypes
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI


PROMPT = """You are evaluating one meme image for hateful content.

First understand the image. Do not classify before describing what is visible.

Step 1: Describe the meme content
- Describe the visible people, objects, scene, symbols, and any relevant visual comparison.
- Transcribe or summarize all readable text.
- Explain how the image and text combine to create the meme's joke, insult, or message.

Step 2: Apply the hateful-content definition
Hate speech refers to a direct or indirect attack against people based on group characteristics, including ethnicity, race, nationality, immigration status, religion, caste, sex, gender identity, sexual orientation, disability, disease, or references that mock hate crimes or evoke suffering associated with historical atrocities.

An attack includes violent or dehumanizing language, claims of inferiority, or calls for exclusion, segregation, or removal.

Classify the meme as hateful if any of the following scenarios are present:
1. The meme mocks, insults, ridicules, humiliates, demeans, or expresses contempt toward a group.
2. The meme uses an identity as the punchline of a joke or negative comparison.
3. The meme uses a country, region, city, district, neighborhood, skyline, public sign, billboard, written language, script, accent, clothing, name, skin color, religious marker, or cultural marker as a proxy for people from a group.
4. The meme assigns a negative stereotype to a group, including stereotypes about behavior, etiquette, intelligence, hygiene, sexuality, criminality, poverty, crowding, migration, consumer habits, disease, or social manners.
5. The meme compares a group or a proxy for that group to animals, especially monkeys, dogs, pigs, rats, insects, or to objects, filth, excrement, disease, vermin, criminals, predators, or something inferior.
6. The meme implies that a group is disgusting, threatening, sexually predatory, invasive, uncivilized, inferior, unwanted, or responsible for social decay.
7. The meme supports, normalizes, jokes about, or implies exclusion, segregation, deportation, removal, violence, denial of rights, or collective punishment against a group.
8. The meme mocks or trivializes suffering connected to genocide, slavery, terrorism, hate crimes, or historical atrocities.
9. The meme targets immigrants, mainlanders, foreigners, tourists, nationalities, ethnic groups, religious groups, racial groups, or sexual-orientation groups with a negative joke or stereotype, even if the wording is indirect or framed as humor.


Important decision rules:
- Memes are often indirect. If the image/text combination implies a group through a place, nationality, language, name, appearance, or cultural marker, treat that as group targeting.
- Do not dismiss identity-based ridicule as merely offensive, crude, or joking. Humor can still be hateful.
- If an identity is plausibly part of the negative joke, prefer hateful.
- Use non-hateful only when the identity is absent or clearly irrelevant to the joke.
- If people are compared to animals, filth, excrement, vermin, or something subhuman, first identify who those people are. If they are linked to a nationality, ethnicity, race, religion, regional-origin group, or a proxy for such a group, classify as hateful.
- If no person is directly shown, but a billboard, sign, text, skyline, district label, tourist label, or other public symbol plausibly stands in for a group, treat that symbol as a proxy.
- When the meme targets "people in a place," decide whether the place is functioning as an identity label rather than a mere location. If the joke depends on that identity label, treat it as group targeting.
- Animalization of generic partygoers is non-hateful only when the joke is clearly about behavior alone and there is no identity, place-based identity, nationality, ethnicity, or regional-origin proxy.

Scoring:
- 0.00-0.29: clearly non-hateful and unrelated to a group
- 0.30-0.69: ambiguous or weak group connection
- 0.70-1.00: group ridicule, stereotype, insult, dehumanization, hostility, exclusion, or atrocity mockery
The classification must be "hateful" when hateful_score >= 0.30; otherwise it must be "non-hateful".

Return only valid JSON with this exact schema:
{
  "visual_description": "concise description of visible image content",
  "text_description": "readable meme text or summary",
  "combined_meaning": "how the image and text create the joke, insult, or message",
  "target": "short target description",
  "group_characteristic": "race | ethnicity | nationality | regional_origin | immigration_status | religion | caste | sex | gender_identity | sexual_orientation | disability | disease | atrocity_reference | tourists | none | unclear",
  "matched_hateful_scenarios": ["scenario numbers that apply, or none"],
  "attack_type": "ridicule | negative_stereotype | insulting_comparison | dehumanization | inferiority | contamination | threat | criminality | sexual_predation | disgust | harm_or_exclusion | atrocity_mockery | none | unclear",
  "explanation": "one concise sentence explaining the classification",
  "hateful_score": 0.0,
  "classification": "hateful or non-hateful"
}"""


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def log(message: str) -> None:
    timestamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"[{timestamp}] {message}", flush=True)


def format_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def image_data_url(path: Path) -> str:
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def classify_image(client: OpenAI, model: str, path: Path, temperature: float, seed: int) -> str:
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        seed=seed,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": image_data_url(path)}},
                ],
            }
        ],
    )
    return response.choices[0].message.content or ""


def result_path_for(result_stem: str) -> Path:
    return Path.cwd() / f"{result_stem}-result.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classify one image for hateful meme content.")
    parser.add_argument("image_path", help="Image file path to classify.")
    parser.add_argument(
        "--result-stem",
        help="Output file stem. Default: input image filename stem.",
    )
    parser.add_argument(
        "--image-label",
        help="Image label to write in the JSONL record. Default: input image filename.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    image_path = Path(args.image_path).expanduser().resolve()
    if not image_path.is_file():
        raise SystemExit(f"Image file not found: {image_path}")
    if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
        extensions = ", ".join(sorted(IMAGE_EXTENSIONS))
        raise SystemExit(f"Unsupported image extension {image_path.suffix!r}; expected one of: {extensions}")

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("Please set OPENROUTER_API_KEY first, e.g. export OPENROUTER_API_KEY=sk-or-...")

    model = os.environ.get("OPENROUTER_MODEL", "openai/gpt-5.4")
    temperature = float(os.environ.get("OPENROUTER_TEMPERATURE", "0"))
    seed = int(os.environ.get("OPENROUTER_SEED", "42"))
    image_label = args.image_label or image_path.name
    result_stem = args.result_stem or image_path.stem
    result_path = result_path_for(result_stem)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        default_headers={
            "HTTP-Referer": "https://local-test.invalid",
            "X-Title": "OpenRouter Image Understanding Test",
        },
    )

    log(f"Model: {model}")
    log(f"Determinism: temperature={temperature}, seed={seed}")
    log(f"Input image: {image_path}")
    log(f"Result file: {result_path}")
    log(f"Image size: {format_bytes(image_path.stat().st_size)}")

    started_at = time.monotonic()
    try:
        output = classify_image(client, model, image_path, temperature, seed)
        elapsed = time.monotonic() - started_at
        log(f"DONE {image_path.name} elapsed={elapsed:.1f}s")
        print("--- model output start ---", flush=True)
        print(output, flush=True)
        print("--- model output end ---", flush=True)
        record = {
            "image": image_label,
            "model": model,
            "temperature": temperature,
            "seed": seed,
            "output": output,
            "elapsed_seconds": round(elapsed, 3),
        }
        exit_code = 0
    except Exception as exc:
        elapsed = time.monotonic() - started_at
        log(f"ERROR {image_path.name} elapsed={elapsed:.1f}s: {exc}")
        record = {
            "image": image_label,
            "model": model,
            "temperature": temperature,
            "seed": seed,
            "error": str(exc),
            "elapsed_seconds": round(elapsed, 3),
        }
        exit_code = 1

    with result_path.open("w", encoding="utf-8") as result_file:
        result_file.write(json.dumps(record, ensure_ascii=False) + "\n")

    log(f"WROTE result for {image_path.name} to {result_path}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

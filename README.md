# hatespeech

## Run the image batch

Generate the batch runner:

```bash
python3 generate_batch_run.py
```

By default this writes a local generated `batch_run.sh` with 4 parallel jobs.
This file is intentionally not committed to the repo. To change the
concurrency, regenerate it with `--max-jobs`:

```bash
python3 generate_batch_run.py --max-jobs 8
```

## OpenRouter API key

The batch script calls the OpenRouter API, so you must set
`OPENROUTER_API_KEY` before running it.

The easiest local setup is to create a `.env` file in the repo root, next to
`README.md`:

```text
hatespeech/
|-- README.md
|-- .env
|-- generate_batch_run.py
`-- images/
```

Put your real OpenRouter key in `.env`:

```bash
export OPENROUTER_API_KEY=sk-or-...
```

Replace `sk-or-...` with your actual key. Do not include quotes unless your key
actually contains spaces, which OpenRouter keys normally do not.

Before running the batch, load `.env` into the current terminal session:

```bash
source .env
```

You can check whether the variable is loaded with:

```bash
echo "$OPENROUTER_API_KEY"
```

If it prints your key, the current terminal session is ready.

The `source .env` command only loads the key for the current terminal session.
If you close the terminal or open a new one, run `source .env` again before
running `bash batch_run.sh`.

You can also skip `.env` and export the key directly in the terminal:

```bash
export OPENROUTER_API_KEY=sk-or-...
```

Do not put your real API key in `README.md`, generated shell scripts, or any
other file that will be committed to Git. The local `.env` file is ignored by
Git through `.gitignore`, but still be careful not to paste your real key into
committed files.

Run the batch:

```bash
bash batch_run.sh
```

The batch runner prints a dependency-free text progress bar as images finish:

```text
[progress] [##########----------] 5/11 45%
```

If any image job fails, the progress line includes the failed count and the
batch exits with a non-zero status after all jobs in flight finish.

Child-process output is redirected away from the screen to keep the progress
log clean. Detailed per-image logs are written to `logs/*.log`, and per-image
JSONL outputs are written to `results/`.

Merge the JSONL result files into a CSV:

```bash
python3 merge_results_to_csv.py
```

This writes `results/results.csv`.

## Run with GitHub Actions

This repo includes a manual GitHub Actions workflow:

```text
.github/workflows/run-hatespeech-batch.yml
```

Before running it, add the OpenRouter key as a GitHub Actions secret:

1. Go to the GitHub repo page.
2. Open `Settings` -> `Secrets and variables` -> `Actions`.
3. Add a new repository secret named `OPENROUTER_API_KEY`.
4. Paste your real OpenRouter key as the secret value.

Then run the workflow manually:

1. Open the repo's `Actions` tab.
2. Select `Run hate speech batch`.
3. Click `Run workflow`.
4. Optionally change `max_jobs` or the OpenRouter `model`.

The workflow will:

1. Install Python and the `openai` package.
2. Generate `batch_run.sh` inside the workflow run.
3. Run the image batch with `OPENROUTER_API_KEY` from GitHub Secrets, including
   progress lines in the Actions log.
4. Merge the JSONL files into `results/results.csv`.
5. Upload only `results/results.csv` as a workflow artifact named
   `hatespeech-results-csv`.

# hatespeech

## Run the image batch

Generate the batch runner:

```bash
python3 generate_batch_run.py
```

By default this writes `batch_run.sh` with 4 parallel jobs. To change the
concurrency, regenerate it with `--max-jobs`:

```bash
python3 generate_batch_run.py --max-jobs 8
```

## OpenRouter API key

The batch script calls the OpenRouter API, so you must set
`OPENROUTER_API_KEY` before running it. Replace `sk-or-...` with your real
OpenRouter key:

```bash
export OPENROUTER_API_KEY=sk-or-...
```

This command only sets the key for the current terminal session. If you close
the terminal or open a new one, run the `export` command again before running
`bash batch_run.sh`.

You can check whether the variable is set with:

```bash
echo "$OPENROUTER_API_KEY"
```

Do not put your real API key in `README.md`, `batch_run.sh`, or any other file
that will be committed to Git. Keep it in your shell environment only.

Run the batch:

```bash
bash batch_run.sh
```

Per-image JSONL outputs are written to `results/`.

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
2. Generate `batch_run.sh`.
3. Run the image batch with `OPENROUTER_API_KEY` from GitHub Secrets.
4. Merge the JSONL files into `results/results.csv`.
5. Upload only `results/results.csv` as a workflow artifact named
   `hatespeech-results-csv`.

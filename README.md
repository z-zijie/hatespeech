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

Set the OpenRouter API key before running the batch:

```bash
export OPENROUTER_API_KEY=sk-or-...
```

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

# LLM-based Intent Translation

Companion repository containing the dataset, experiment scripts, and results for translating natural-language network intents into Prolog facts for [DIPS](dips/README.md). Experiments compare Qwen2.5 models (3B, 7B, and 14B) and Gemini using zero-shot and few-shot prompting, plus LoRA adaptation for Qwen2.5.

**[Results dashboard](https://di-unipi-socc.github.io/llm-based-intent-translation/)** · [Dashboard guide](docs/README.md) · [Dataset](dataset/) · [Result tables](data/) · [Prompt templates](references/prompts.txt)

Explore the results in the hosted dashboard or [run the dashboard locally](#view-the-dashboard-locally).

## Start here

| To explore… | Open |
| --- | --- |
| Individual predictions, scores, errors, and generation times | [Dashboard guide](docs/README.md) and [dashboard source](docs/) |
| Natural-language intents and human reference facts | [Intent dataset](dataset/); [example intent](dataset/context1/intentA.txt) and [reference facts](dataset/context1/facts.pl) |
| Available virtual network functions | [VNF catalogue](dataset/catalogoVNF.json) |
| Run-level results and error records | [run_table.parquet](data/run_table.parquet) and [error_table.parquet](data/error_table.parquet) |
| Prompts and error categories | [prompts.txt](references/prompts.txt) and [error_description.txt](references/error_description.txt) |
| Local-model prompting experiments | [Qwen2.5 in-context learning](experiments/local/in_context/) |
| Local-model training and evaluation | [Qwen2.5 LoRA](experiments/local/lora/) |
| Cloud-model experiments | [Gemini scripts](experiments/cloud/) |
| Fact comparison and DIPS execution | [Evaluation scripts](scripts/) and [DIPS](dips/) |

## Dataset and results

The dataset contains **34 scenarios**, each expressed in three ways: **102 intent formulations** in total. Each `dataset/contextN/` directory contains `intentA.txt`, `intentB.txt`, `intentC.txt`, and a shared `facts.pl` reference specification.

- **A:** the complete service chain precedes its properties.
- **B:** each chain fragment is followed by its properties.
- **C:** properties precede the chain fragment to which they apply.

The formulations change information order while preserving the intended facts. Scenario identifiers link equivalent variants; the 102 formulations are not 102 independent scenarios.

The dashboard provides three views: **Run Explorer** for an individual translation, **Aggregate** for grouped results, and **Compare Techniques** for comparisons across settings. Filters select model, technique, scenario, and formulation. The URL hash retains the current selection for sharing. The appearance selector offers Light, Dark, and System modes and remembers the selection in the browser. Reported execution times measure **model generation only**, excluding DIPS processing.

The Parquet files are the source tables. `docs/data.js` is their browser-ready export; it omits the large DIPS execution trace while retaining the fields used by the dashboard.

## View the dashboard locally

From the repository root, with Python installed:

```bash
python3 -m http.server 8000
```

Open <http://localhost:8000/docs/>. Browsing the checked-in dashboard requires no model downloads, GPU, or Python packages.

After changing either Parquet table, regenerate the browser data:

```bash
make install
make data
```

## Dashboard publication

The [results dashboard](https://di-unipi-socc.github.io/llm-based-intent-translation/) is hosted on GitHub Pages from `docs/`. Its HTML, CSS, JavaScript, and exported data are served as static files.

To update the dashboard after modifying the Parquet tables, run `make data` and commit the resulting `docs/data.js` with the source tables. Changes pushed to `docs/` are published automatically; publication does not regenerate data.

## DIPS dependency

The `dips/` directory contains the DIPS sources and the benchmark configuration. Compared with upstream commit `dc0620d5aca0cc0c7f657c9fc32299590219475c`, `dips.pl` selects the added `data/infrastructures/InfrTestingIntent.pl`; `data/services/all.pl` disables two example service imports and adds `authVF`. The batch executor uses this directory directly.

Use `make data` to regenerate browser data and `make serve` to preview the published site at <http://localhost:8000/>.

## Experiment code

```text
dataset/                        # Scenarios, formulations, reference facts, VNF catalogue
data/                           # Run and error tables
docs/                           # Static dashboard published by GitHub Pages
experiments/
  cloud/                        # Gemini prompting and evaluation
  local/
    in_context/                 # 0-, 3-, and 9-shot experiments, across model sizes
    lora/                       # Five-fold training, inference, and evaluation
scripts/                        # Shared metrics, error analysis, DIPS execution, and data export
dips/                           # Prolog rules and DIPS documentation
references/                     # Prompt templates and error taxonomy
```

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run from the repository root:

```bash
make install
```

This runs `uv sync --locked --all-groups`. The root `pyproject.toml` declares analysis/export dependencies (`pandas`, `pyarrow`), a `cloud` group (`google-generativeai`, `google-api-core`), and a `local` group for training and inference (`torch`, `torchvision`, `transformers`, `datasets`, `trl`, `unsloth`, and their supporting libraries).

Python 3.11 or 3.12 is required. Local-model dependencies are installed only on Linux x86_64; these experiments require an NVIDIA GPU and a driver compatible with the locked PyTorch 2.6 / CUDA 12.4 stack. On macOS and other platforms, `make install` installs analysis and cloud dependencies; CUDA training is unavailable. The local stack is pinned for compatibility with the scripts' `SFTTrainer` API. The lockfile specifies the software environment for running these scripts; the exact environment used to produce the stored results was not recorded. To install only dashboard/export dependencies, use `uv sync --locked`.

SWI-Prolog (`swipl`) is a separate system dependency required for DIPS; uv does not install it. Gemini scripts read the `GEMINI_API_KEY` environment variable. Run scripts through the project environment (for example `uv run --locked --group cloud python experiments/cloud/prompt_zeroShot/run_gemini.py`), or activate `.venv` before using `python`. Local-model commands below require the supported GPU host and access to the model weights.

Default input, output, and checkpoint paths are resolved relative to each script. Run the experiment entry points from the repository root:

```bash
# Qwen2.5 prompting experiments
uv run --locked --group local python experiments/local/in_context/run_all_pipelines.py
```

```bash
# Qwen2.5 LoRA training and inference
uv run --locked --group local python experiments/local/lora/run_all_pipelines.py
```

These commands start model experiments and may require substantial GPU time and model downloads. For analysis of existing results, use the dashboard or Parquet tables instead. Cloud experiment entry points are under [prompt_zeroShot](experiments/cloud/prompt_zeroShot/) and [prompt_fewShot](experiments/cloud/prompt_fewShot/). Shared evaluation tools include [fact metrics](scripts/fact_metrics.py), [error analysis](scripts/error_catalog.py), and [DIPS execution](scripts/dips_executor.py).

## Project context

The original experimental framework was developed by **Niccolò Baicchi** as thesis work at the **University of Pisa**. DIPS processes declarative network intents expressed as Prolog facts.

## Data compatibility

Stored datasets, results, scenario identifiers, and prompt templates are preserved in their recorded form. Timing records retain their original filenames and JSON keys, including `tempi_esecuzione.json`, `durata_secondi`, and timestamp fields. The evaluation scripts read this format directly.

# Results dashboard guide

[Open the dashboard](https://di-unipi-socc.github.io/llm-based-intent-translation/) · [Repository overview](../README.md)

The dashboard explores stored LLM translations of network intents into Prolog facts, their evaluation scores, and downstream DIPS outcomes. It reads the exported results in `data.js`; browsing does not run a model or execute DIPS.

## Navigation and controls

- **Model:** choose Gemini or a Qwen2.5 model size. Only recorded model/technique combinations are available; LoRA is available for Qwen models.
- **Technique:** select Zero-shot, 3-shot, 9-shot, or LoRA in Run Explorer and Aggregate. Compare Techniques displays the available settings together.
- **Context:** select one of the 34 service scenarios in Run Explorer or the Side-by-Side Inspector. The previous/next buttons and left/right arrow keys move between contexts. Keyboard shortcuts are inactive while a text input or theme radio is focused.
- **Schema:** choose formulation A, B, or C of the same scenario. A presents the complete chain before its properties; B interleaves chain fragments and properties; C presents properties before their chain fragment.
- **Appearance:** one circular button cycles through System (computer, default), Light (sun), and Dark (moon with stars), then returns to System. Its tooltip names the current mode and the next one. System follows the device colour scheme; the browser remembers your choice.

The URL records the selected view and filters. Copy the address to share a selection or bookmark it. Appearance is a browser preference and is not included in shared links.

## Run Explorer

Inspect one translation, selected by model, technique, context, and schema.

The run header shows its identifier, DIPS outcome, exact-match status, and error count. The metric row shows recall, precision, fact-set Jaccard, F1, placement Jaccard, and model generation time.

Below the metrics, the natural-language intent is followed by **Generated output** and **Expected output (gold)**, displayed side by side with Prolog highlighting and line numbers. Copy buttons copy the corresponding text or run identifier.

The **Error catalogue** groups detected errors by type, subtype, and severity, with occurrence counts. **Compare Techniques** opens the Side-by-Side Inspector for the current model, context, and schema.

## Aggregate

Summarise all recorded contexts and schemas for one model/technique combination. Context and schema controls are hidden in this view.

- **Summary metrics:** mean fact-level scores, exact-match rate, mean placement Jaccard, mean generation time, and errors per run. Counts identify the runs included in each statistic.
- **DIPS outcome:** distribution of successful solutions, no-solution results, and execution errors.
- **Errors by type:** counts for syntax errors, wrong values, wrong VNFs, and insertions/removals, separated by High and Low severity.
- **Errors by subtype:** a more detailed frequency table, including how many runs are affected.
- **F1-score per context & schema:** a heatmap of individual translations, with a purple-to-teal-to-yellow scale from F1 = 0 to F1 = 1. Hover for details; click a recorded cell to open that run. The legend identifies missing runs and DIPS failures.

**Compare Techniques for [model]** opens the benchmark comparison for the selected model.

## Compare Techniques

Compare the available adaptation settings for one model. This tab has two views.

### Benchmark Overview

Compare aggregate results across techniques. Choose **All Schemas**, **Schema A**, **Schema B**, or **Schema C** to filter the comparison.

The overview shows exact-match rates and supporting metrics for each technique. The comparison matrix reports translation scores, DIPS results, generation times, and error statistics; **Best** marks the preferred value among the displayed settings for that metric. Changes relative to zero-shot are shown where available.

Additional panels compare DIPS outcome distributions, sensitivity to the three formulations, and error counts by category. Technique counts can differ because demonstration scenarios are excluded from few-shot test sets; inspect the displayed denominators when comparing settings.

### Side-by-Side Inspector

Compare translations of the same context and schema across techniques. The intent appears once above the generated outputs. Expand **Show Expected Output** to inspect the shared reference facts.

Each technique column contains its output, exact-match status, F1, DIPS outcome, generation time, and error summary. **Copy** copies that output; **Open** returns to its Run Explorer view. Missing combinations are identified explicitly.

## Reading scores and outcomes

| Item | Meaning |
| --- | --- |
| Precision | Fraction of generated normalized facts that match the reference. |
| Recall | Fraction of reference normalized facts recovered by the translation. |
| F1-score | Harmonic mean of precision and recall. |
| Jaccard | Intersection divided by union of generated and reference fact sets. |
| Exact match | Generated and reference fact sets match after evaluation normalization, and DIPS reports no error. Aggregate views report the fraction of matching runs. |
| Jaccard DIPS | Recorded overlap between placement sets obtained from generated and reference facts. Missing values appear as a dash; means use non-missing values and display their coverage. |
| Inference time / Mean Latency | Model generation time in seconds, excluding DIPS processing. |
| DIPS Solution | DIPS found a placement solution. This does not imply exact translation or agreement with the reference placement set. |
| DIPS False | DIPS returned no solution. |
| High / Low errors | Severity assigned by the error classifier. Low errors include stricter constraints; they do not establish placement feasibility. |

Scores generally range from 0 to 1; exact-match and solution rates are also displayed as percentages. Error counts measure occurrences, not necessarily distinct affected runs. The 102 formulations represent 34 underlying scenarios, rather than 102 independent services.

The export excludes runs with flagged DIPS errors from exact matches, including identifier errors missed by fact normalization. Original Parquet tables remain unchanged.

See the [error taxonomy](../references/error_description.txt), [fact metrics implementation](../scripts/fact_metrics.py), and [source tables](../data/) for evaluation details.

## Local preview

From the repository root, run:

```bash
make serve
```

Open <http://localhost:8000/>. No Python packages or GPU are needed to browse the stored dashboard. To rebuild `data.js` from the Parquet tables, follow the [repository instructions](../README.md#view-the-dashboard-locally).

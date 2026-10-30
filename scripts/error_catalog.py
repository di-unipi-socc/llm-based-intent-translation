"""
error_catalog.py — LLM Error Catalog on IBN Prolog Facts
========================================================================

Classifies each difference between Gold Standard and LLM Prediction into 4 categories:
    A. SYNTAX        — structural errors (dots, parentheses, arity)          → High
    B. WRONG VALUES  — type/value-unit/hard-soft mismatch                    → High
       Low Severity Exceptions: soft→hard (stricter constraint),
                                lower latency or higher bandwidth (stricter constraint)
    C. WRONG VNFs    — topology, target chain, edge/cloud assignment         → High
    D. INSERTIONS/REMOVALS — extra or missing facts (FP / FN)                → High

Automatically traverses all output folders in the workspace, detects
prediction files (pattern 'output_context*' and 'context*_intent*'), pairs them
with the gold standard in dataset/ and produces a summary report.

It uses the same set logic of the experiment evaluation scripts
and fact_metrics.py for extraction and normalization of facts.
"""

import os
import re
import sys
from collections import defaultdict

# ---------------------------------------------------------------------------
#  Import the existing metrics module
# ---------------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import fact_metrics as metrics  # noqa: E402

# ---------------------------------------------------------------------------
#  CONFIGURATION
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)  # project root (IBN github/)
DATASET_DIR = os.path.join(BASE_DIR, "dataset")




# ============================================================================
#  STRUCTURE FOR ACCUMULATING ERRORS
# ============================================================================
class ErrorEntry:
    """Single cataloged error entry."""
    def __init__(self, category, subtype, severity, description,
                 generated_fact="", gold_fact="", source_file=""):
        self.category = category       # "A", "B", "C", "D"
        self.subtype = subtype       # e.g. "UNBALANCED_PARENTHESES"
        self.severity = severity           # "High" or "Low"
        self.description = description   # human-readable string
        self.generated_fact = generated_fact
        self.gold_fact = gold_fact
        self.source_file = source_file

    def __repr__(self):
        return (f"[{self.category}.{self.subtype}/{self.severity}] "
                f"{self.description}")


# ============================================================================
#  A. SYNTACTIC ANALYSIS (on raw text, disconnected from Gold Standard)
# ============================================================================

# Expected arity for each predicate
_EXPECTED_ARITIES = {
    "intent": 4,
    "target": 2,
    "vnf": 3,
    "vnfXUser": 4,
}


def check_syntax_errors(raw_text, source_file=""):
    """
    Analyzes the raw text of the LLM file for Prolog syntax errors.
    Every non-empty, non-comment line that doesn't respect the Prolog format
    is reported as a category A / SYNTAX error.

    Returns a list of category A ErrorEntry.
    """
    errors = []
    lines = raw_text.strip().split("\n")

    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Ignore Prolog comments
        if line_stripped.startswith("%"):
            continue

        # Missing final dot
        if not line_stripped.endswith("."):
            errors.append(ErrorEntry(
                category="A", subtype="SYNTAX", severity="High",
                description=f"Line {i}: missing final dot → '{line_stripped}'",
                generated_fact=line_stripped, source_file=source_file
            ))

        # Unbalanced parentheses
        content = line_stripped.rstrip(".")
        if content.count("(") != content.count(")"):
            errors.append(ErrorEntry(
                category="A", subtype="SYNTAX", severity="High",
                description=f"Line {i}: unbalanced round parentheses → '{line_stripped}'",
                generated_fact=line_stripped, source_file=source_file
            ))
        if content.count("[") != content.count("]"):
            errors.append(ErrorEntry(
                category="A", subtype="SYNTAX", severity="High",
                description=f"Line {i}: unbalanced square parentheses → '{line_stripped}'",
                generated_fact=line_stripped, source_file=source_file
            ))

        # Arity mismatch
        match = re.match(r'^([a-zA-Z0-9_]+)\((.*)\)\s*\.\s*$', line_stripped)
        if match:
            predicate = match.group(1)
            args = _parse_args(match.group(2))
            num_args = len(args)

            if predicate == "propertyExpectation":
                if num_args not in (6, 9):
                    errors.append(ErrorEntry(
                        category="A", subtype="SYNTAX", severity="High",
                        description=(f"Line {i}: propertyExpectation has {num_args} "
                                     f"parameters (expected 6 or 9) → '{line_stripped}'"),
                        generated_fact=line_stripped, source_file=source_file
                    ))
            elif predicate in _EXPECTED_ARITIES:
                expected = _EXPECTED_ARITIES[predicate]
                if num_args != expected:
                    errors.append(ErrorEntry(
                        category="A", subtype="SYNTAX", severity="High",
                        description=(f"Line {i}: {predicate} has {num_args} "
                                     f"parameters (expected {expected}) → '{line_stripped}'"),
                        generated_fact=line_stripped, source_file=source_file
                    ))

    return errors



# ============================================================================
#  MATCHING AND CLASSIFICATION (Cat. B values, Cat. C vnf, Cat. D ins/rem)
# ============================================================================
def _parse_args(args_str):
    """
    Parses the arguments string of a Prolog fact,
    correctly handling lists [...] and tuples (...).
    Returns a list of strings (one element per parameter).
    """
    args = []
    bracket_level = 0
    paren_level = 0
    current_arg = ""

    for char in args_str:
        if char == "[":
            bracket_level += 1
            current_arg += char
        elif char == "]":
            bracket_level -= 1
            current_arg += char
        elif char == "(":
            paren_level += 1
            current_arg += char
        elif char == ")":
            paren_level -= 1
            current_arg += char
        elif char == "," and bracket_level == 0 and paren_level == 0:
            args.append(current_arg.strip())
            current_arg = ""
        else:
            current_arg += char

    if current_arg.strip():
        args.append(current_arg.strip())

    return args


def _parse_fact(fact_str):
    """
    Parses a normalized fact (without arbitrary IDs) in the format
    'predicate(arg1, arg2, ...)' returning (predicate, [arg1, arg2, ...]).
    """
    match = re.match(r'^([a-zA-Z0-9_]+)\((.*)\)$', fact_str)
    if not match:
        return fact_str, []
    return match.group(1), _parse_args(match.group(2))


def _parse_raw_fact(line):
    """
    Parses a raw Prolog fact (with final dot) returning
    (predicate, [arg1, arg2, ...]) or (None, []) if malformed.
    """
    line = line.strip().rstrip(".")
    match = re.match(r'^([a-zA-Z0-9_]+)\((.*)\)$', line)
    if not match:
        return None, []
    return match.group(1), _parse_args(match.group(2))


def classify_parameter_diff(predicate, param_index, val_llm, val_gold,
                            args_llm, args_gold, generated_fact_string, gold_fact_string,
                            source_file=""):
    """
    Given a parameter that differs between LLM and Gold, determines the category
    and subtype of the error.

    The logic depends on the predicate and the position of the parameter:

    For NORMALIZED propertyExpectation (without first 2 IDs):
      - Non-changing parameters (7 args): Type, Operator, hard/soft, Value, Unit, SourceVNF, DestVNF
        index:                             0      1         2        3     4       5          6
      - Changing parameters (4 args):      Type, _, Source, Dest
        index:                             0    1    2      3

    For NORMALIZED intent (without starting and ending ID):
      - args: ProviderOp, NumUsers
        index:    0           1

    For NORMALIZED target:
      - args: [vnf list]
        index:   0

    For vnf / vnfXUser: not normalized, all parameters visible.
    """
    # ---------- propertyExpectation ----------
    if predicate == "propertyExpectation":
        num_args = len(args_gold)  # use gold as reference

        if num_args == 7:
            # Non-changing: Type(0), Operator(1), hard/soft(2), Value(3), Unit(4), SrcVNF(5), DstVNF(6)
            if param_index == 0:
                return "B", "TYPE_MISMATCH", "High", \
                    f"Wrong type: '{val_llm}' instead of '{val_gold}'"
            elif param_index == 2 and val_llm in ("hard", "soft") and val_gold in ("hard", "soft"):
                # hard instead of soft → stricter constraint → Low
                # soft instead of hard → looser constraint → High
                if val_llm == "hard" and val_gold == "soft":
                    return "B", "HARD_SOFT_MISMATCH", "Low", \
                        f"Wrong Hard/Soft: '{val_llm}' instead of '{val_gold}' (stricter constraint)"
                else:
                    return "B", "HARD_SOFT_MISMATCH", "High", \
                        f"Wrong Hard/Soft: '{val_llm}' instead of '{val_gold}'"
            elif param_index in (1, 2, 3, 4):
                # For param_index==3 (Value) in non-changing properties,
                # check if the error is "benign" (stricter constraint):
                #   - latency: LLM value lower than Gold → Low
                #   - bandwidth: LLM value higher than Gold → Low
                if param_index == 3 and len(args_gold) > 0:
                    property_type = args_gold[0].strip().lower()
                    try:
                        v_llm = float(val_llm)
                        v_gold = float(val_gold)
                        if property_type == "latency" and v_llm < v_gold:
                            return "B", "VALUE_UNIT_MISMATCH", "Low", \
                                f"Lower latency: '{val_llm}' instead of '{val_gold}' (stricter constraint)"
                        elif property_type == "bandwidth" and v_llm > v_gold:
                            return "B", "VALUE_UNIT_MISMATCH", "Low", \
                                f"Higher bandwidth: '{val_llm}' instead of '{val_gold}' (stricter constraint)"
                    except (ValueError, TypeError):
                        pass  # non-numeric values → stays High
                return "B", "VALUE_UNIT_MISMATCH", "High", \
                    f"Wrong Value/Unit (param {param_index+1}): '{val_llm}' instead of '{val_gold}'"
            elif param_index in (5, 6):
                # In 9-parameter properties, Source and Dest are always
                # interchangeable (VNF link constraints or affinity):
                # a pure swap DOES NOT constitute an error.
                other_idx = 6 if param_index == 5 else 5
                val_llm_other = args_llm[other_idx] if other_idx < len(args_llm) else ""
                val_gold_other = args_gold[other_idx] if other_idx < len(args_gold) else ""
                if val_llm == val_gold_other and val_llm_other == val_gold:
                    return None  # Source/Dest swap accepted: no error
                return "C", "TOPOLOGY_ERROR", "High", \
                    f"Wrong VNF (param {param_index+1}): '{val_llm}' instead of '{val_gold}'"

        elif num_args == 4:
            # Changing: Type(0), _(1), Source(2), Dest(3)
            if param_index == 0:
                return "B", "TYPE_MISMATCH", "High", \
                    f"Wrong Type: '{val_llm}' instead of '{val_gold}'"
            elif param_index == 1:
                return "B", "VALUE_UNIT_MISMATCH", "High", \
                    f"Wrong 4th parameter placeholder: '{val_llm}' instead of '{val_gold}'"
            elif param_index in (2, 3):
                # Check if it's a Source↔Dest swap
                other_idx = 3 if param_index == 2 else 2
                val_llm_other = args_llm[other_idx] if other_idx < len(args_llm) else ""
                val_gold_other = args_gold[other_idx] if other_idx < len(args_gold) else ""
                if val_llm == val_gold_other and val_llm_other == val_gold:
                    return "C", "SOURCE_DEST_SWAP", "High", \
                        f"Source/Dest swapped: LLM has ({args_llm[2]},{args_llm[3]}) instead of ({args_gold[2]},{args_gold[3]})"
                return "C", "TOPOLOGY_ERROR", "High", \
                    f"Wrong VNF (param {param_index+1}): '{val_llm}' instead of '{val_gold}'"

        # Fallback for unexpected arity (but still matched)
        return "B", "VALUE_UNIT_MISMATCH", "High", \
            f"Wrong parameter {param_index+1}: '{val_llm}' instead of '{val_gold}'"

    # ---------- intent ----------
    if predicate == "intent":
        # Normalized: ProviderOp(0), NumUsers(1)
        if param_index == 0:
            return "B", "VALUE_UNIT_MISMATCH", "High", \
                f"Wrong ProviderOp: '{val_llm}' instead of '{val_gold}'"
        elif param_index == 1:
            return "B", "VALUE_UNIT_MISMATCH", "High", \
                f"Wrong NumUsers: '{val_llm}' instead of '{val_gold}'"
        return "B", "VALUE_UNIT_MISMATCH", "High", \
            f"Wrong intent parameter: '{val_llm}' instead of '{val_gold}'"

    # ---------- target ----------
    if predicate == "target":
        return "C", "WRONG_TARGET_CHAIN", "High", \
            f"Wrong Target chain: '{val_llm}' instead of '{val_gold}'"

    # ---------- vnf / vnfXUser ----------
    if predicate in ("vnf", "vnfXUser"):
        # vnf: VnfID(0), edge/cloud(1), HW(2)
        # vnfXUser: VnfID(0), l(1), (1,N)(2), HW(3)
        if param_index == 0:
            return "C", "TOPOLOGY_ERROR", "High", \
                f"Wrong VnfID: '{val_llm}' instead of '{val_gold}'"
        elif predicate == "vnf" and param_index == 1:
            return "C", "WRONG_ASSIGNMENT", "High", \
                f"Wrong placement: '{val_llm}' instead of '{val_gold}'"
        elif predicate == "vnf" and param_index == 2:
            return "C", "WRONG_ASSIGNMENT", "High", \
                f"Wrong Hardware: '{val_llm}' instead of '{val_gold}'"
        elif predicate == "vnfXUser":
            return "C", "WRONG_ASSIGNMENT", "High", \
                f"Wrong vnfXUser parameter (pos {param_index+1}): '{val_llm}' instead of '{val_gold}'"

    # Generic fallback
    return "B", "VALUE_UNIT_MISMATCH", "High", \
        f"Wrong parameter {param_index+1}: '{val_llm}' instead of '{val_gold}'"


def match_and_classify(gold_facts, generated_facts, source_file=""):
    """
    Set logic: computes leftovers, pairs facts by predicate + best-match,
    classifies every differing parameter in categories B/C, and unpaired facts
    in category D.

    Returns a list of ErrorEntry.
    """
    errors = []

    # Facts in common → no error
    # Leftovers
    leftovers_gs = gold_facts - generated_facts       # Gold facts missing in LLM
    leftovers_llm = generated_facts - gold_facts      # Extra LLM facts (not in gold)

    if not leftovers_gs and not leftovers_llm:
        return errors  # perfect match

    # -------------------------------------------------------------------
    #  PHASE 1: Pairing by predicate + best-match
    # -------------------------------------------------------------------
    matched_gs = set()
    matched_llm = set()

    for llm_fact in sorted(leftovers_llm):
        llm_pred, llm_args = _parse_fact(llm_fact)

        best_match = None
        best_score = -1
        best_diffs = []

        for gs_fact in sorted(leftovers_gs):
            if gs_fact in matched_gs:
                continue

            gs_pred, gs_args = _parse_fact(gs_fact)

            # They must have the same predicate to be paired
            if llm_pred != gs_pred:
                continue

            # Compute similarity score (number of identical parameters)
            max_len = max(len(llm_args), len(gs_args))
            if max_len == 0:
                continue

            score = 0
            diffs = []
            for idx in range(max_len):
                val_llm = llm_args[idx] if idx < len(llm_args) else "<missing>"
                val_gs = gs_args[idx] if idx < len(gs_args) else "<missing>"
                if val_llm == val_gs:
                    score += 1
                else:
                    diffs.append((idx, val_llm, val_gs))

            if score > best_score:
                best_score = score
                best_match = gs_fact
                best_diffs = diffs

        # If a match is found, classify the parameter differences
        if best_match is not None and best_score > 0:
            matched_gs.add(best_match)
            matched_llm.add(llm_fact)

            gs_pred, gs_args = _parse_fact(best_match)
            for (idx, val_llm, val_gs) in best_diffs:
                result = classify_parameter_diff(
                    llm_pred, idx, val_llm, val_gs,
                    llm_args, gs_args,
                    llm_fact, best_match, source_file
                )
                if result is None:
                    continue
                cat, subtype, severity, desc = result
                errors.append(ErrorEntry(
                    category=cat,
                    subtype=subtype,
                    severity=severity,
                    description=desc,
                    generated_fact=llm_fact,
                    gold_fact=best_match,
                    source_file=source_file
                ))

    # -------------------------------------------------------------------
    #  PHASE 2: Unpaired facts → Insertions (D) and Removals (D)
    # -------------------------------------------------------------------
    # Insertions: facts in LLM without correspondent in gold
    for llm_fact in sorted(leftovers_llm - matched_llm):
        errors.append(ErrorEntry(
            category="D",
            subtype="INSERTION",
            severity="High",
            description=f"Extra fact generated by LLM (False Positive): '{llm_fact}'",
            generated_fact=llm_fact,
            gold_fact="",
            source_file=source_file
        ))

    # Removals: gold facts not generated by LLM
    for gs_fact in sorted(leftovers_gs - matched_gs):
        errors.append(ErrorEntry(
            category="D",
            subtype="REMOVAL",
            severity="High",
            description=f"Gold fact not generated by LLM (False Negative): '{gs_fact}'",
            generated_fact="",
            gold_fact=gs_fact,
            source_file=source_file
        ))

    return errors


# ============================================================================
#  COMPLETE ANALYSIS OF A SINGLE FILE
# ============================================================================
def analyze_file(generated_file_path, gold_file_path):
    """
    Complete analysis of a single LLM file vs Gold Standard.

    Pass 1: Syntax analysis on raw text (Cat. A)
    Pass 2: Normalized set comparison (Cat. B.values + C + D)

    Returns a list of ErrorEntry.
    """
    file_label = os.path.basename(generated_file_path)

    # Read the raw LLM text
    try:
        with open(generated_file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except FileNotFoundError:
        return [ErrorEntry("A", "FILE_NOT_FOUND", "High",
                           f"LLM File not found: {generated_file_path}",
                           source_file=file_label)]

    # ----- PASS 1: syntactic errors -----
    errors = check_syntax_errors(raw_text, source_file=file_label)

    # ----- PASS 2: normalized set comparison -----
    gold_facts = metrics.extract_fact_set(gold_file_path)
    generated_facts = metrics.extract_fact_set(generated_file_path)

    errors += match_and_classify(gold_facts, generated_facts, source_file=file_label)

    return errors


# ============================================================================
#  DISCOVERY AND MAIN LOOP
# ============================================================================
def find_output_files(dir_path):
    """
    Searches for all LLM output files in a directory.
    Detects two naming patterns:
    - 'output_contextN_intentX.txt' (Qwen folders)
    - 'contextN_intentX.txt' (Gemini folders)

    Returns a list of tuples (file_path, context_name, intent_letter).
    """
    results = []

    try:
        files = os.listdir(dir_path)
    except OSError:
        return results

    for f in sorted(files):
        if not f.endswith(".txt"):
            continue
        # Skip report files that have already been generated
        if f.startswith("report"):
            continue

        # Pattern 1: output_context10_intentA.txt (Qwen)
        match = re.match(r'output_(context\d+)_intent([A-Za-z]+)\.txt', f)
        if match:
            results.append((
                os.path.join(dir_path, f),
                match.group(1),
                match.group(2)
            ))
            continue

        # Pattern 2: context10_intentA.txt (Gemini)
        match = re.match(r'(context\d+)_intent([A-Za-z]+)\.txt', f)
        if match:
            results.append((
                os.path.join(dir_path, f),
                match.group(1),
                match.group(2)
            ))

    return results


# List of categories and names (used everywhere in reports)
CATEGORY_ORDER = ["A", "B", "C", "D"]
CATEGORY_NAMES = {
    "A": "A. SYNTAX",
    "B": "B. WRONG VALUES",
    "C": "C. WRONG VNFs",
    "D": "D. INSERTIONS/REMOVALS"
}


def generate_report(errors_by_model, output_path):
    """
    Generates the summary report with error frequency and severity,
    aggregated by model and by category.

    errors_by_model: dict { "model_name": [ErrorEntry, ...] }
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("LLM ERROR CATALOG — SUMMARY REPORT\n")
        f.write("=" * 80 + "\n\n")

        # ---- GLOBAL AGGREGATE ----
        all_errors = []
        for errs in errors_by_model.values():
            all_errors.extend(errs)

        _write_report_section(f, "GLOBAL AGGREGATE", all_errors)

        # ---- PER MODEL ----
        for model_name, errors in sorted(errors_by_model.items()):
            f.write("\n" + "=" * 80 + "\n")
            _write_report_section(f, f"MODEL: {model_name}", errors)

    print(f"\n=> Error catalog report saved at: {output_path}")


def generate_model_report(model_name, errors_by_file, output_path):
    """
    Generates a detailed report for a single model/test.

    errors_by_file: dict { "file_name": [ErrorEntry, ...] }
                     Includes files with 0 errors (empty list) as well.
    output_path: path to the report file to be created.
    """
    all_errors = []
    for errs in errors_by_file.values():
        all_errors.extend(errs)

    files_with_errors = {f: errs for f, errs in errors_by_file.items() if errs}
    files_without_errors = [f for f, errs in errors_by_file.items() if not errs]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write(f"ERROR CATALOG — {model_name}\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Analyzed files:     {len(errors_by_file)}\n")
        f.write(f"Files with errors:  {len(files_with_errors)}\n")
        f.write(f"Files without errors: {len(files_without_errors)}\n")
        f.write(f"Total errors:       {len(all_errors)}\n\n")

        # ---- SUMMARY OF FILES WITH ERRORS ----
        f.write("-" * 80 + "\n")
        f.write("SUMMARY OF FILES WITH ERRORS\n")
        f.write("-" * 80 + "\n\n")

        files_with_only_low_errors = []

        if files_with_errors:
            for filename in sorted(files_with_errors.keys()):
                errs = files_with_errors[filename]
                high_count = sum(1 for e in errs if e.severity == "High")
                low_count = sum(1 for e in errs if e.severity == "Low")
                
                if high_count == 0 and low_count > 0:
                    files_with_only_low_errors.append(filename)

                count = {cat: 0 for cat in CATEGORY_ORDER}
                for e in errs:
                    count[e.category] = count.get(e.category, 0) + 1
                category_summary = ", ".join(
                    f"{cat}={count.get(cat, 0)}" for cat in CATEGORY_ORDER
                )

                f.write(f"  {filename:45s} : {len(errs):3d} errors (High={high_count}, Low={low_count}) ({category_summary})\n")
        else:
            f.write("  No files with errors!\n")
        f.write("\n")

        # ---- FILES WITH ONLY LOW ERRORS ----
        f.write("-" * 80 + "\n")
        f.write("FILES WITH ONLY LOW ERRORS\n")
        f.write("-" * 80 + "\n\n")

        if files_with_only_low_errors:
            for filename in sorted(files_with_only_low_errors):
                f.write(f"  ✓ {filename}\n")
        else:
            f.write("  No files with only low errors.\n")
        f.write("\n")

        # ---- AGGREGATED STATISTICS ----
        f.write("-" * 80 + "\n")
        f.write("AGGREGATED STATISTICS\n")
        f.write("-" * 80 + "\n")
        _write_report_section(f, model_name, all_errors)

        # ---- ERROR DETAIL PER FILE ----
        f.write("\n" + "-" * 80 + "\n")
        f.write("ERROR DETAIL PER FILE\n")
        f.write("-" * 80 + "\n\n")

        for filename in sorted(files_with_errors.keys()):
            errs = files_with_errors[filename]
            f.write(f"  [{filename}] — {len(errs)} errors\n")
            for e in errs:
                f.write(f"    [{e.category}.{e.subtype}/{e.severity}] {e.description}\n")
            f.write("\n")

    print(f"  => Single report saved at: {output_path}")


def _write_report_section(f, title, errors):
    """
    Writes a section of the report for a given set of errors.
    Includes: counts by category, subtype, severity, and top examples.
    """
    f.write(f"\n--- {title} ---\n")
    f.write(f"Total cataloged errors: {len(errors)}\n\n")

    if not errors:
        f.write("No errors found.\n")
        return

    # Count by CATEGORY
    category_counts = defaultdict(int)
    for e in errors:
        category_counts[e.category] += 1

    f.write("  FREQUENCY BY CATEGORY:\n")
    for cat in CATEGORY_ORDER:
        count = category_counts.get(cat, 0)
        pct = (count / len(errors) * 100) if errors else 0
        f.write(f"    {CATEGORY_NAMES.get(cat, cat):30s} : {count:5d}  ({pct:5.1f}%)\n")
    f.write("\n")

    # Count by SUBTYPE
    subtype_counts = defaultdict(int)
    for e in errors:
        key = f"{e.category}.{e.subtype}"
        subtype_counts[key] += 1

    f.write("  FREQUENCY BY SUBTYPE:\n")
    for key, count in sorted(subtype_counts.items(),
                                 key=lambda x: -x[1]):
        pct = (count / len(errors) * 100) if errors else 0
        f.write(f"    {key:40s} : {count:5d}  ({pct:5.1f}%)\n")
    f.write("\n")

    # Count by SEVERITY
    high_count = sum(1 for e in errors if e.severity == "High")
    low_count = sum(1 for e in errors if e.severity == "Low")
    f.write("  SEVERITY DISTRIBUTION:\n")
    f.write(f"    {'High (modifies network intent)':40s} : {high_count:5d}  ({high_count/len(errors)*100:5.1f}%)\n")
    f.write(f"    {'Low (fixable in post-processing)':40s} : {low_count:5d}  ({low_count/len(errors)*100:5.1f}%)\n")
    f.write("\n")

    # Count by SEVERITY per CATEGORY
    f.write("  SEVERITY PER CATEGORY:\n")
    for cat in CATEGORY_ORDER:
        cat_errs = [e for e in errors if e.category == cat]
        if not cat_errs:
            continue
        high_category_count = sum(1 for e in cat_errs if e.severity == "High")
        low_category_count = sum(1 for e in cat_errs if e.severity == "Low")
        f.write(f"    {CATEGORY_NAMES.get(cat, cat):30s} : High={high_category_count:4d}, Low={low_category_count:4d}\n")
    f.write("\n")




def main():
    """
    Entry point: traverses all folders in the workspace, detects LLM
    output files, compares them with gold standards, and generates the report.
    It also generates single reports for each model in a dedicated folder.
    """
    print("=" * 60)
    print("=== LLM ERROR CATALOG — Starting analysis ===")
    print("=" * 60)

    errors_by_model = {}
    # Map: model_name → { file_name: [ErrorEntry, ...] }
    errors_by_model_and_file = {}
    # Map: model_name → model directory (for info)
    model_directories = {}
    analyzed_file_count = 0

    # Traverse all subfolders looking for output files
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip gold standard folder, __pycache__, .git and reports_catalogo
        basename = os.path.basename(root)
        if basename in ("dataset", ".cache", ".venv", "docs", "__pycache__", ".git", "error_reports", "reports_catalogo", "dips_results", "risultati_dips", "dips"):
            dirs.clear()  # do not descend into subfolders
            continue

        output_files = find_output_files(root)
        if not output_files:
            continue

        # Determine the model name from the folder structure
        # e.g. "3-shot/.../Qwen2.5-14b" → "3-shot/Qwen2.5-14b"
        rel_path = os.path.relpath(root, BASE_DIR)
        path_parts = rel_path.replace("\\", "/").split("/")
        # Try to extract a meaningful name
        model_name = "/".join(p for p in path_parts
                                if not p.endswith("-001") and p != ".")
        if not model_name:
            model_name = rel_path

        print(f"\nAnalysis: {model_name} ({len(output_files)} files)")

        model_errors = []
        errors_by_file = {}  # for the single report

        for file_path, context_name, intent_letter in output_files:
            # Find the corresponding gold standard
            gold_path = os.path.join(DATASET_DIR,
                                     context_name, "facts.pl")
            if not os.path.exists(gold_path):
                print(f"  ⚠ Gold standard not found for {context_name}")
                continue

            filename = os.path.basename(file_path)
            errors = analyze_file(file_path, gold_path)
            model_errors.extend(errors)
            errors_by_file[filename] = errors
            analyzed_file_count += 1

        # Summary by model
        if model_errors:
            counts = {cat: sum(1 for e in model_errors if e.category == cat)
                        for cat in CATEGORY_ORDER}
            summary = ", ".join(f"{cat}={counts[cat]}" for cat in CATEGORY_ORDER)
            print(f"  Total errors: {len(model_errors)} ({summary})")

        errors_by_model[model_name] = model_errors
        errors_by_model_and_file[model_name] = errors_by_file
        model_directories[model_name] = root

    # ---- Generate the global report ----
    print(f"\n{'=' * 60}")
    print(f"Analyzed files: {analyzed_file_count}")

    report_path = os.path.join(BASE_DIR, "error_catalog_report.txt")
    generate_report(errors_by_model, report_path)

    # ---- Generate single reports in the dedicated folder ----
    reports_dir = os.path.join(BASE_DIR, "error_reports")
    os.makedirs(reports_dir, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"Generating single reports in: {reports_dir}")

    for model_name in sorted(errors_by_model_and_file.keys()):
        errors_by_file = errors_by_model_and_file[model_name]
        # Create a valid file name from the model name
        # e.g. "3-shot/Qwen2.5-3b" → "3-shot_Qwen2.5-3b"
        report_filename = model_name.replace("/", "_").replace("\\", "_")
        model_report_path = os.path.join(
            reports_dir, f"report_{report_filename}.txt"
        )
        generate_model_report(model_name, errors_by_file, model_report_path)

    print(f"\n{'=' * 60}")
    print("Processing completed!")


# ============================================================================
if __name__ == "__main__":
    main()

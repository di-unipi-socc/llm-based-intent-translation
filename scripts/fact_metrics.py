import os
import re

# ==============================================================================
#  PROLOG PARSING
# ==============================================================================

def extract_target_list(prolog_text):
    """Extracts the VNF list from the target/2 predicate (e.g. target(_, [fw, ids]) → ['fw','ids'])."""
    match = re.search(r"target\([^,]+,\s*\[(.*?)\]\)", prolog_text)
    return [v.strip() for v in match.group(1).split(',') if v.strip()] if match else []


def build_vnf_mapping(vnf_list):
    """Maps each VNF to the normalized name: {fw: vnf_0, ids: vnf_1, ...}."""
    return {vnf: f"vnf_{i}" for i, vnf in enumerate(vnf_list)}


# ==============================================================================
#  PREDICATE NORMALIZATION
# ==============================================================================

def _norm_property_expectation(args):
    """Removes Rule ID and Intent ID (first 2 parameters).
    
    For 'affinity dedicated' properties, sorts the last two VNF parameters
    (SourceVNF, DestVNF) alphabetically because they are interchangeable.
    """
    parts = args.split(',')
    if len(parts) <= 2:
        return args
    norm = parts[2:]
    # norm has 7 elements: Type, Operator, hard/soft, Value, Unit, SourceVNF, DestVNF
    # If Type == 'affinity' and Value == 'dedicated', sort SourceVNF and DestVNF
    if len(norm) == 7:
        property_type = norm[0].strip()
        value = norm[3].strip()
        if property_type == 'affinity' and value == 'dedicated':
            norm[-2], norm[-1] = sorted([norm[-2].strip(), norm[-1].strip()])
    return ",".join(norm)


def _norm_intent(args):
    """Removes Intent ID (first) and Target ID (last)."""
    parts = args.split(',')
    return ",".join(parts[1:-1]) if len(parts) > 2 else args


def _norm_target(args):
    """Keeps only the list inside square brackets."""
    match = re.search(r'\[(.*?)\]', args)
    return f"[{match.group(1)}]" if match else args


# Dispatch: predicate → argument normalization function
_NORMALIZERS = {
    'propertyExpectation': _norm_property_expectation,
    'intent':              _norm_intent,
    'target':              _norm_target,
}


def normalize_arguments(predicate, raw_arguments):
    """Applies specific normalization to the predicate, if defined."""
    args = re.sub(r'\s+', ' ', raw_arguments).replace(', ', ',').strip()
    normalizer = _NORMALIZERS.get(predicate)
    return normalizer(args) if normalizer else args


# ==============================================================================
#  FACT SET EXTRACTION
# ==============================================================================

def extract_fact_set(file_path):
    """Reads a .pl file, extracts Prolog facts and normalizes them (VNF + arbitrary IDs)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"❌ Error: The file {file_path} does not exist!")
        return set()

    text = re.sub(r'%.*', '', text)                    # remove comments
    # vnf_mapping = build_vnf_mapping(extract_target_list(text))

    facts = set()
    for m in re.finditer(r"([a-zA-Z0-9_]+)\((.*?)\)\.", text):
        predicate, arguments = m.group(1).strip(), m.group(2)

        # VNF NORMALIZATION HAS BEEN DISABLED
        # for original, normalized in vnf_mapping.items():
        #     arguments = re.sub(rf'\b{re.escape(orig)}\b', norm, arguments)

        args_norm = normalize_arguments(predicate, arguments)
        if args_norm:
            facts.add(f"{predicate}({args_norm})")

    return facts


def set_to_string(s):
    """Formats a set of facts as an ordered string, one line per fact."""
    return "\n".join(sorted(s)) if s else "No facts found (Empty set)"


# ==============================================================================
#  EVALUATION METRICS
# ==============================================================================

def calculate_jaccard(gold_facts, generated_facts):
    """Jaccard: |I ∩ L| / |I ∪ L|  — penalizes omissions and hallucinations."""
    if not gold_facts and not generated_facts: return 1.0
    if not gold_facts or  not generated_facts: return 0.0
    return round(len(gold_facts & generated_facts) / len(gold_facts | generated_facts), 4)


def calculate_recall(gold_facts, generated_facts):
    """Recall: |I ∩ L| / |I|  — measures LLM omissions."""
    if not gold_facts: return 1.0
    if not generated_facts:    return 0.0
    return round(len(gold_facts & generated_facts) / len(gold_facts), 4)


def calculate_precision(gold_facts, generated_facts):
    """Precision: |I ∩ L| / |L|  — measures LLM hallucinations."""
    if not generated_facts and not gold_facts: return 1.0
    if not generated_facts:                    return 0.0
    return round(len(gold_facts & generated_facts) / len(generated_facts), 4)


def calculate_f1(precision, recall):
    """F1-Score: harmonic mean between Precision and Recall."""
    return round(2 * precision * recall / (precision + recall), 4) if (precision + recall) else 0.0


def calculate_accuracy(metric_pairs):
    """Accuracy: number of perfect elements / total number of elements.
    
    An element is 'perfect' if it has precision == 1.0 and recall == 1.0.
    
    Args:
        metric_pairs: list of tuples (precision, recall) for each element of the test set.
    
    Returns:
        Accuracy rounded to 4 decimals.
    """
    if not metric_pairs:
        return 0.0
    perfect_count = sum(1 for p, r in metric_pairs if p == 1.0 and r == 1.0)
    return round(perfect_count / len(metric_pairs), 4)


# ==============================================================================
#  MAIN
# ==============================================================================

if __name__ == "__main__":
    GOLD_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset", "context1", "facts.pl")
    FILE_LLM    = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset", "context2", "facts.pl")

    gold_facts = extract_fact_set(GOLD_FILE)
    generated_facts    = extract_fact_set(FILE_LLM)

    print("=== PROLOG SEMANTIC EVALUATOR ===\n")
    print("--- Ideal Extracted Facts ---")
    print(set_to_string(gold_facts), "\n")
    print("--- LLM Extracted Facts ---")
    print(set_to_string(generated_facts), "\n")

    recall    = calculate_recall(gold_facts, generated_facts)
    precision = calculate_precision(gold_facts, generated_facts)
    jaccard   = calculate_jaccard(gold_facts, generated_facts)
    f1        = calculate_f1(precision, recall)

    print("==================================================")
    print("📊 LOGICAL EVALUATION RESULTS")
    print("==================================================")
    print(f"✅ Recall      (Omissions)     : {recall}")
    print(f"🎯 Precision   (Hallucinations) : {precision}")
    print(f"⚖️  Jaccard     (Global)        : {jaccard}")
    print(f"🏆 F1-Score    (Balance)       : {f1}")
    print("==================================================")

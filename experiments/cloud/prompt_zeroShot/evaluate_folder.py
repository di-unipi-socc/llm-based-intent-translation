import os
import sys
import re
import json

# Dynamically calculate the project root and add scripts/ to the path
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, "../../.."))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "scripts"))
# pyrefly: ignore [missing-import]
import fact_metrics as metrics

# pyrefly: ignore [missing-import]
import catalog_parser


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(_PROJECT_ROOT, "dataset")


def analyze_fact_differences(gold_facts, generated_facts):
    """
    Extracts the differences (removing perfect matches), associates generated facts with 
    the most similar gold facts and identifies which parameters differ.
    Returns:
    - error_details: dictionary {generated_fact: string_with_error}
    - unmatched_omissions: set of gold facts that found no association
    """
    missing_facts = gold_facts - generated_facts
    extra = generated_facts - gold_facts
    
    def parse_fact(fact_str):
        match = re.match(r'^([a-zA-Z0-9_]+)\((.*)\)$', fact_str)
        if not match:
            return fact_str, []
        pred = match.group(1)
        args_str = match.group(2)
        args = []
        bracket_level = 0
        current_arg = ""
        for char in args_str:
            if char == '[':
                bracket_level += 1
                current_arg += char
            elif char == ']':
                bracket_level -= 1
                current_arg += char
            elif char == ',' and bracket_level == 0:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += char
        if current_arg:
            args.append(current_arg.strip())
        return pred, args

    error_details = {}
    matched_missing_facts = set()
    
    for ex in extra:
        ex_pred, ex_args = parse_fact(ex)
        best_match = None
        best_score = -1
        best_diffs = []
        
        for man in missing_facts:
            if man in matched_missing_facts:
                continue
                
            man_pred, man_args = parse_fact(man)
            if ex_pred != man_pred:
                continue
                
            score = 0
            diffs = []
            max_len = max(len(ex_args), len(man_args))
            for i in range(max_len):
                extra_arg = ex_args[i] if i < len(ex_args) else "<missing>"
                missing_arg = man_args[i] if i < len(man_args) else "<missing>"
                if extra_arg == missing_arg:
                    score += 1
                else:
                    diffs.append(f"wrong parameter {i+1} (expected: '{missing_arg}')")
                    
            if score > best_score:
                best_score = score
                best_match = man
                best_diffs = diffs
                
        if best_match is not None:
            matched_missing_facts.add(best_match)
            detail = "Error: " + ", ".join(best_diffs)
            error_details[ex] = detail
        else:
            error_details[ex] = "Hallucination (no corresponding gold predicate)"
            
    unmatched_omissions = missing_facts - matched_missing_facts
    return error_details, unmatched_omissions


def evaluate_folder(dir_path, vnf_map):
    """
    Searches for all output files in a single folder (e.g. a 'result' folder),
    creates the individual report for each file and finally creates a folder report
    (evaluation_report.txt) with the averages of all files found in THAT folder.
    """
    # Identify all output files in the current folder
    output_files = [f for f in os.listdir(dir_path) if f.startswith("context") and f.endswith(".txt")]
    
    if not output_files:
        return
        
    print(f"\nAnalyzing folder: {dir_path}")
    
    # Load the execution times file, if present
    timing_path = os.path.join(dir_path, "tempi_esecuzione.json")
    execution_times = {}
    if os.path.exists(timing_path):
        try:
            with open(timing_path, "r", encoding="utf-8") as timing_file:
                execution_times = json.load(timing_file)
            print(f"  Loaded execution times from: {timing_path}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"  Warning: error loading times: {e}")
    
    total_recall = 0.0
    total_precision = 0.0
    total_jaccard = 0.0
    total_f1 = 0.0
    test_count = 0
    accuracy_pairs = []  # list of (precision, recall) for each item
    total_time = 0.0
    time_count = 0
    
    for file_name in sorted(output_files):
        # We extract context and intent letter
        match = re.search(r'(context\d+)_intent([A-Za-z]+)\.txt', file_name)
        if not match:
            continue
            
        context_name = match.group(1)
        intent_letter = match.group(2)
        
        file_path = os.path.join(dir_path, file_name)
        gold_file_path = os.path.join(DATASET_DIR, context_name, "facts.pl")
        intent_text_file = os.path.join(DATASET_DIR, context_name, f"intent{intent_letter}.txt")
        
        if not os.path.exists(gold_file_path):
            print(f"  Warning: ideal file not found for {context_name} ({gold_file_path})")
            continue
            
        # Reading and enrichment of the textual intent
        intent_text = "Intent text not found."
        if os.path.exists(intent_text_file):
            with open(intent_text_file, "r", encoding="utf-8") as intent_file:
                intent_text = intent_file.read().strip()
                
            if vnf_map:
                intent_text = catalog_parser.enrich_intent_with_hardware(intent_text, vnf_map)
                
        # Metrics calculation
        gold_facts = metrics.extract_fact_set(gold_file_path)
        generated_facts = metrics.extract_fact_set(file_path)
        
        recall = metrics.calculate_recall(gold_facts, generated_facts)
        precision = metrics.calculate_precision(gold_facts, generated_facts)
        jaccard = metrics.calculate_jaccard(gold_facts, generated_facts)
        f1 = metrics.calculate_f1(precision, recall)
        
        print(f"  [{context_name} intent{intent_letter}] R: {recall:.4f} | P: {precision:.4f} | J: {jaccard:.4f} | F1: {f1:.4f}")
        
        # Recover execution time for this file
        timing_info = execution_times.get(file_name, {})
        execution_time = timing_info.get("durata_secondi", None)
        if execution_time is not None:
            total_time += execution_time
            time_count += 1
        
        # Collect the (precision, recall) pair for accuracy calculation
        accuracy_pairs.append((precision, recall))
        
        # Sum for averages
        total_recall += recall
        total_precision += precision
        total_jaccard += jaccard
        total_f1 += f1
        test_count += 1
        
        # INDIVIDUAL REPORT
        report_name = f"report_{context_name}_intent{intent_letter}.txt"
        report_path = os.path.join(dir_path, report_name)
        
        with open(report_path, "w", encoding="utf-8") as report_file:
            report_file.write(f"RESULTS FOR {context_name.upper()} - INTENT {intent_letter.upper()}\n")
            report_file.write(f"Analyzed file: {file_name}\n")
            report_file.write("==================================================\n")
            report_file.write("--- TEXTUAL INTENT ---\n")
            report_file.write(f"{intent_text}\n")
            report_file.write("==================================================\n")
            report_file.write(f"Recall    (Omissions)     : {recall:.4f}\n")
            report_file.write(f"Precision (Hallucinations): {precision:.4f}\n")
            report_file.write(f"Jaccard   (Global)        : {jaccard:.4f}\n")
            report_file.write(f"F1-Score  (Balance)       : {f1:.4f}\n")
            if execution_time is not None:
                report_file.write(f"Execution Time            : {execution_time:.4f}s\n")
                report_file.write(f"Start: {timing_info.get('timestamp_inizio', 'N/A')} | End: {timing_info.get('timestamp_fine', 'N/A')}\n")
            report_file.write("==================================================\n\n")
            
            # If metrics are perfect, simply print the facts
            if recall == 1.0 and precision == 1.0:
                report_file.write("--- Ideal Extracted Facts ---\n")
                report_file.write(metrics.set_to_string(gold_facts) + "\n\n")
                report_file.write("--- LLM Extracted Facts ---\n")
                report_file.write(metrics.set_to_string(generated_facts) + "\n")
            else:
                # If they are not perfect, apply the detailed analysis function
                error_details, omissions = analyze_fact_differences(gold_facts, generated_facts)
                
                report_file.write("--- Ideal Extracted Facts (Gold) ---\n")
                report_file.write(metrics.set_to_string(gold_facts) + "\n\n")
                
                report_file.write("--- LLM Extracted Facts (Analysis) ---\n")
                correct_facts = gold_facts & generated_facts
                
                # Correct facts
                for c in sorted(correct_facts):
                    report_file.write(f"{c}  [ Correct]\n")
                    
                # Wrong/extra facts (annotated)
                extra = generated_facts - gold_facts
                for ex in sorted(extra):
                    note = error_details.get(ex, "")
                    report_file.write(f"{ex}  [ {note}]\n")
                    
                # Omissions not associated with anything (left behind)
                if omissions:
                    report_file.write("\n--- Missing Gold Facts (Absolute omissions) ---\n")
                    for om in sorted(omissions):
                        report_file.write(f"{om}  [ Fact not generated by LLM]\n")
            
    # FOLDER REPORT
    if test_count > 0:
        avg_recall = total_recall / test_count
        avg_precision = total_precision / test_count
        avg_jaccard = total_jaccard / test_count
        avg_f1 = total_f1 / test_count
        accuracy = metrics.calculate_accuracy(accuracy_pairs)
        perfect_count = sum(1 for p, r in accuracy_pairs if p == 1.0 and r == 1.0)
        
        folder_report_path = os.path.join(dir_path, "evaluation_report.txt")
        with open(folder_report_path, "w", encoding="utf-8") as output_file_handle:
            output_file_handle.write(f"AVERAGE FOLDER RESULTS OVER {test_count} TESTS\n")
            output_file_handle.write("==================================================\n")
            output_file_handle.write(f"Average Recall      : {avg_recall:.4f}\n")
            output_file_handle.write(f"Average Precision   : {avg_precision:.4f}\n")
            output_file_handle.write(f"Average Jaccard     : {avg_jaccard:.4f}\n")
            output_file_handle.write(f"Average F1-Score    : {avg_f1:.4f}\n")
            output_file_handle.write(f"Accuracy            : {accuracy:.4f}  ({perfect_count}/{test_count} perfect)\n")
            if time_count > 0:
                avg_time = total_time / time_count
                output_file_handle.write(f"Avg Execution Time  : {avg_time:.4f}s  (over {time_count} tests)\n")
                output_file_handle.write(f"Total Execution Time: {total_time:.4f}s\n")
            output_file_handle.write("==================================================")
            
        print(f"  -> Accuracy: {accuracy:.4f} ({perfect_count}/{test_count} perfect)")
        if time_count > 0:
            avg_time = total_time / time_count
            print(f"  -> Avg time: {avg_time:.4f}s | Total time: {total_time:.4f}s")
        print(f"  -> Created folder report: {folder_report_path}")


def main():
    catalog_json = os.path.join(DATASET_DIR, "catalogoVNF.json")

    # Load the catalog only once
    try:
        vnf_map = catalog_parser.load_vnf_catalog(catalog_json)
    except FileNotFoundError:
        print(f"Warning: VNF catalog not found at {catalog_json}. The intent text will not be enriched.")
        vnf_map = {}

    print("=" * 60)
    print("=== SINGLE REPORTS AND FOLDER REPORT GENERATION ===")
    print("=" * 60)

    # Scan all folders within BASE_DIR
    for root, dirs, files in os.walk(BASE_DIR):
        evaluate_folder(root, vnf_map)

    print("\nProcessing completed!")


if __name__ == "__main__":
    main()

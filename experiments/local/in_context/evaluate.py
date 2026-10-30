import os
import sys
import re
import json

# Dynamically calculates the project root and adds scripts/ to the path
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
    Extracts differences (removing perfect matches), associates generated facts to the
    most similar gold facts and identifies which parameters differ.
    Returns:
    - error_details: dictionary {generated_fact: error_string}
    - unassociated_omissions: set of gold facts that found no association
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
                    diffs.append(f"parameter {i+1} wrong (expected: '{missing_arg}')")
                    
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
    Searches all output files in a single folder (e.g. a 'result' folder),
    creates the individual report for each file and finally creates a global report
    (evaluation_report.txt) with the averages of all files found in THAT folder.
    
    Returns a dictionary with the average metrics of the folder, or None
    if there are no output files to analyze.
    """
    # Identify all output files in the current folder
    output_files = [f for f in os.listdir(dir_path) if f.startswith("output_context") and f.endswith(".txt")]
    
    if not output_files:
        return None
        
    print(f"\nFolder analysis: {dir_path}")
    
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
    accuracy_pairs = []  # List of (precision, recall) pairs for each item
    total_time = 0.0
    time_count = 0
    
    for file_name in sorted(output_files):
        # Extract context and intent letter
        match = re.search(r'output_(context\d+)_intent([A-Za-z]+)\.txt', file_name)
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
            
        # Reading and enrichment of textual intent
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
        
        # Retrieve execution time for this file
        timing_info = execution_times.get(file_name, {})
        execution_time = timing_info.get("durata_secondi", None)
        if execution_time is not None:
            total_time += execution_time
            time_count += 1
        
        # Collect the (precision, recall) pair for accuracy calculation
        accuracy_pairs.append((precision, recall))
        
        # Sum for folder averages
        total_recall += recall
        total_precision += precision
        total_jaccard += jaccard
        total_f1 += f1
        test_count += 1
        
        # 1) INDIVIDUAL REPORT
        report_name = f"report_{context_name}_intent{intent_letter}.txt"
        report_path = os.path.join(dir_path, report_name)
        
        with open(report_path, "w", encoding="utf-8") as report_file:
            report_file.write(f"RESULTS FOR {context_name.upper()} - INTENT {intent_letter.upper()}\n")
            report_file.write(f"Analyzed file: {file_name}\n")
            report_file.write("==================================================\n")
            report_file.write("--- INTENT TEXT ---\n")
            report_file.write(f"{intent_text}\n")
            report_file.write("==================================================\n")
            report_file.write(f"Recall    (Omissions)     : {recall:.4f}\n")
            report_file.write(f"Precision (Hallucinations) : {precision:.4f}\n")
            report_file.write(f"Jaccard   (Global)       : {jaccard:.4f}\n")
            report_file.write(f"F1-Score  (Balance)    : {f1:.4f}\n")
            if execution_time is not None:
                report_file.write(f"Execution Time          : {execution_time:.4f}s\n")
                report_file.write(f"Start: {timing_info.get('timestamp_inizio', 'N/A')} | End: {timing_info.get('timestamp_fine', 'N/A')}\n")
            report_file.write("==================================================\n\n")
            
            # If the metrics are perfect, simply print the facts
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
                    
                # Omissions not matched to a generated fact
                if omissions:
                    report_file.write("\n--- Missing Gold Facts (Unmatched Omissions) ---\n")
                    for om in sorted(omissions):
                        report_file.write(f"{om}  [ Fact not generated by LLM]\n")
            
    # 2) GLOBAL FOLDER REPORT
    if test_count > 0:
        avg_recall = total_recall / test_count
        avg_precision = total_precision / test_count
        avg_jaccard = total_jaccard / test_count
        avg_f1 = total_f1 / test_count
        accuracy = metrics.calculate_accuracy(accuracy_pairs)
        num_perfect = sum(1 for p, r in accuracy_pairs if p == 1.0 and r == 1.0)
        
        folder_report_path = os.path.join(dir_path, "evaluation_report.txt")
        with open(folder_report_path, "w", encoding="utf-8") as output_file_handle:
            output_file_handle.write(f"AVERAGE FOLDER RESULTS ON {test_count} TESTS\n")
            output_file_handle.write("==================================================\n")
            output_file_handle.write(f"Average Recall      : {avg_recall:.4f}\n")
            output_file_handle.write(f"Average Precision   : {avg_precision:.4f}\n")
            output_file_handle.write(f"Average Jaccard     : {avg_jaccard:.4f}\n")
            output_file_handle.write(f"Average F1-Score    : {avg_f1:.4f}\n")
            output_file_handle.write(f"Accuracy          : {accuracy:.4f}  ({num_perfect}/{test_count} perfect)\n")
            if time_count > 0:
                avg_time = total_time / time_count
                output_file_handle.write(f"Average Exec. Time : {avg_time:.4f}s  (on {time_count} tests)\n")
                output_file_handle.write(f"Total Exec. Time: {total_time:.4f}s\n")
            output_file_handle.write("==================================================")
            
        print(f"  -> Accuracy: {accuracy:.4f} ({num_perfect}/{test_count} perfect)")
        if time_count > 0:
            print(f"  -> Average time: {avg_time:.4f}s | Total time: {total_time:.4f}s")
        print(f"  -> Created global report for folder: {folder_report_path}")
        
        return {
            "folder": dir_path,
            "num_test": test_count,
            "recall": avg_recall,
            "precision": avg_precision,
            "jaccard": avg_jaccard,
            "f1": avg_f1,
            "accuracy": accuracy,
            "num_perfect": num_perfect,
            "total_time": total_time,
            "average_time": total_time / time_count if time_count > 0 else None,
            "timed_count": time_count,
        }
    
    return None


def generate_cross_validation_report(folder_results, output_path):
    """
    Generates a global report with the average of metrics of all folders
    analyzed in the 5-fold cross-validation.
    """
    if not folder_results:
        print("No results to aggregate for the 5-fold report.")
        return
    
    n = len(folder_results)
    avg_recall = sum(r["recall"] for r in folder_results) / n
    avg_precision = sum(r["precision"] for r in folder_results) / n
    avg_jaccard = sum(r["jaccard"] for r in folder_results) / n
    avg_f1 = sum(r["f1"] for r in folder_results) / n
    total_tests = sum(r["num_test"] for r in folder_results)
    total_perfect = sum(r["num_perfect"] for r in folder_results)
    overall_accuracy = round(total_perfect / total_tests, 4) if total_tests > 0 else 0.0
    avg_accuracy_per_fold = sum(r["accuracy"] for r in folder_results) / n
    
    # Global times calculation
    results_with_times = [r for r in folder_results if r.get("average_time") is not None]
    overall_total_time = sum(r["total_time"] for r in results_with_times)
    overall_time_count = sum(r["timed_count"] for r in results_with_times)
    overall_avg_time = overall_total_time / overall_time_count if overall_time_count > 0 else None
    
    with open(output_path, "w", encoding="utf-8") as output_file_handle:
        output_file_handle.write("5-FOLDS CROSS-VALIDATION GLOBAL REPORT\n")
        output_file_handle.write("=" * 60 + "\n\n")
        output_file_handle.write(f"Number of analyzed folds: {n}\n")
        output_file_handle.write(f"Total number of tests: {total_tests}\n\n")
        
        output_file_handle.write("--- FOLDER DETAIL ---\n\n")
        for r in folder_results:
            folder_name = os.path.basename(os.path.dirname(r["folder"]))
            output_file_handle.write(f"  {folder_name} ({r['num_test']} test)\n")
            output_file_handle.write(f"    Recall: {r['recall']:.4f} | Precision: {r['precision']:.4f} | ")
            output_file_handle.write(f"Jaccard: {r['jaccard']:.4f} | F1: {r['f1']:.4f} | ")
            output_file_handle.write(f"Accuracy: {r['accuracy']:.4f} ({r['num_perfect']}/{r['num_test']})")
            if r.get("average_time") is not None:
                output_file_handle.write(f" | Average Time: {r['average_time']:.4f}s")
            output_file_handle.write("\n\n")
        
        output_file_handle.write("=" * 60 + "\n")
        output_file_handle.write(f"GLOBAL AVERAGES ON {n} FOLDS ({total_tests} total tests)\n")
        output_file_handle.write("=" * 60 + "\n")
        output_file_handle.write(f"Average Recall      : {avg_recall:.4f}\n")
        output_file_handle.write(f"Average Precision   : {avg_precision:.4f}\n")
        output_file_handle.write(f"Average Jaccard     : {avg_jaccard:.4f}\n")
        output_file_handle.write(f"Average F1-Score    : {avg_f1:.4f}\n")
        output_file_handle.write(f"Accuracy Global  : {overall_accuracy:.4f}  ({total_perfect}/{total_tests} perfect)\n")
        output_file_handle.write(f"Average Accuracy/Fold: {avg_accuracy_per_fold:.4f}\n")
        if overall_avg_time is not None:
            output_file_handle.write(f"Average Exec. Time : {overall_avg_time:.4f}s  (on {overall_time_count} test)\n")
            output_file_handle.write(f"Total Exec. Time: {overall_total_time:.4f}s\n")
        output_file_handle.write("=" * 60 + "\n")
    
    print(f"\n=> 5-fold global report saved in: {output_path}")


def main():
    catalog_json = os.path.join(DATASET_DIR, "catalogoVNF.json")

    # We load the catalog only once
    try:
        vnf_map = catalog_parser.load_vnf_catalog(catalog_json)
    except FileNotFoundError:
        print(f"Warning: VNF catalog not found in {catalog_json}. Intents text will not be enriched.")
        vnf_map = {}

    print("=" * 60)
    print("=== SINGLE REPORTS AND FOLDER GLOBAL REPORT GENERATION ===")
    print("=" * 60)

    folder_results = []

    # Scan all folders inside BASE_DIR
    for root, dirs, files in os.walk(BASE_DIR):
        result = evaluate_folder(root, vnf_map)
        if result is not None:
            folder_results.append(result)

    # Generate the 5-fold global report
    report_5fold_path = os.path.join(BASE_DIR, "cross_validation_report.txt")
    generate_cross_validation_report(folder_results, report_5fold_path)

    print("\nProcessing completed!")


if __name__ == "__main__":
    main()


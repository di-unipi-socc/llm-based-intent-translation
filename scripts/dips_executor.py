import subprocess
import os
import re
import sys
import shutil

# ==============================================================================
# PATHS AND PARAMETERS CONFIGURATION
# ==============================================================================
# Script folder (scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Project root (IBN github/) — LLM files scanning starts from here
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# DIPS installation folder (contains dips.pl)
DIPS_DIR = os.path.join(BASE_DIR, "dips")

# Root folder in which to create DIPS results subfolders
OUTPUT_BASE_DIR = os.path.join(SCRIPT_DIR, "dips_results")

# Timeout in seconds for each Prolog execution
TIMEOUT_SECONDS = 15


# ==============================================================================
# SWI-PROLOG EXECUTABLE DETECTION
# ==============================================================================
def find_swipl_executable():
    """
    Searches for the SWI-Prolog executable (swipl) in the system PATH
    or in the default installation paths on Windows/Linux.
    """
    # 1. Check in the system PATH
    swipl_in_path = shutil.which("swipl")
    if swipl_in_path:
        return swipl_in_path

    # 2. Standard paths on Windows
    windows_paths = [
        r"C:\Program Files\swipl\bin\swipl.exe",
        r"C:\Program Files (x86)\swipl\bin\swipl.exe",
        r"C:\swipl\bin\swipl.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\swipl\bin\swipl.exe"),
    ]
    for p in windows_paths:
        if os.path.isfile(p):
            return p

    # 3. Default fallback
    return "swipl"


# ==============================================================================
# EXTRACTING INFORMATION FROM PROLOG / TXT FILES
# ==============================================================================
def extract_intent_id(file_path):
    """Extracts the intent ID from the first parameter of the intent/4 predicate."""
    pattern = re.compile(r"intent\(\s*'?([a-zA-Z0-9_]+)'?\s*,")
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    return match.group(1)
    except OSError:
        return None
    return None


def extract_target_list(file_path):
    """Extracts the VNF list from the target/2 predicate."""
    pattern = re.compile(r"target\([^,]+,\s*\[(.*?)\]\)")
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    vnfs = [v.strip() for v in match.group(1).split(',') if v.strip()]
                    return vnfs
    except OSError:
        return []
    return []


# ==============================================================================
# SCANNING LLM GENERATED FOLDERS AND FILES
# ==============================================================================
def extract_sort_key(filename):
    """
    Extracts a numeric key to sort files naturally:
    e.g. 'output_context2_intentA.txt' -> (2, 'A')
    """
    m = re.search(r'context(\d+)_intent([A-Za-z0-9_]+)', filename)
    if m:
        return (int(m.group(1)), m.group(2))
    return (999999, filename)


def find_llm_files(dir_path):
    """
    Finds all LLM generated files in a specific folder:
    - 'output_contextN_intentX.txt' (Qwen)
    - 'contextN_intentX.txt' (Gemini)
    
    Returns a list of tuples: (file_name, full_path)
    sorted naturally by context and intent.
    """
    results = []
    try:
        files = os.listdir(dir_path)
    except OSError:
        return results

    for f in files:
        if not f.endswith(".txt"):
            continue
        if f.startswith("report"):
            continue

        # Check if it matches one of the two formats
        if re.match(r'^(output_)?context\d+_intent[A-Za-z0-9_]+\.txt$', f):
            results.append((f, os.path.join(dir_path, f)))

    results.sort(key=lambda x: extract_sort_key(x[0]))
    return results


def build_output_folder_name(rel_path):
    """
    Converts a relative path (e.g. '3-shot-.../3-shot/Qwen2.5-3b')
    into a clean and readable folder name (e.g. '3-shot_Qwen2.5-3b').
    """
    path_parts = rel_path.replace("\\", "/").split("/")
    filtered_parts = [p for p in path_parts if not p.endswith("-001") and p != "."]
    if filtered_parts:
        return "_".join(filtered_parts)
    return rel_path.replace("\\", "_").replace("/", "_")


def discover_llm_folders(base_dir):
    """
    Recursively explores base_dir and returns a dictionary:
    { clean_model_name: (source_folder, file_list) }
    """
    discovered_folders = {}
    ignored_folders = {
        "dataset",
        ".cache",
        ".venv",
        "docs",
        "error_reports",
        "reports_catalogo",
        "dips_results",
        "risultati_dips",
        "__pycache__",
        ".git",
        "dips",
        "scratch"
    }

    for root, dirs, files in os.walk(base_dir):
        # Skip special folders
        basename = os.path.basename(root)
        if basename in ignored_folders:
            dirs.clear()
            continue

        generated_file = find_llm_files(root)
        if generated_file:
            rel_path = os.path.relpath(root, base_dir)
            model_name = build_output_folder_name(rel_path)
            discovered_folders[model_name] = (root, generated_file)

    return discovered_folders


# ==============================================================================
# SINGLE FILE EXECUTION IN DIPS
# ==============================================================================
def execute_dips(dips_dir, file_pl, output_text_file, swipl_bin="swipl", timeout=TIMEOUT_SECONDS):
    """
    Executes DIPS for a single Prolog/TXT file generated by LLM:
    1. Extracts the intent_id and target from the file.
    2. Calls SWI-Prolog executing the goal: consult(file), dips(intent_id, Output), writeln(Output).
    3. Saves the result in output_text_file with format:
       - Line 1: TARGET:<vnf1,vnf2,...>
       - Following lines: DIPS output or error message.
    
    Returns an outcome string: 'SOLUTION', 'FALSE', 'PROLOG_ERROR', 'TIMEOUT', 'INTENT_ERROR', 'SWIPL_ERROR'
    """
    intent_id = extract_intent_id(file_pl)
    target_list = extract_target_list(file_pl)
    target_str = ",".join(target_list) if target_list else "NO_TARGET"

    # Make sure the output folder exists
    os.makedirs(os.path.dirname(output_text_file), exist_ok=True)

    if not intent_id:
        with open(output_text_file, 'w', encoding='utf-8') as f:
            f.write(f"TARGET:{target_str}\n")
            f.write("ERROR:\nUnable to find the intent ID in the file.\n")
        return "INTENT_ERROR"

    # In Prolog on Windows, paths with backslashes must be normalized with slashes /
    prolog_path = os.path.abspath(file_pl).replace("\\", "/")
    goal = f"consult('{prolog_path}'), dips('{intent_id}', Output), writeln(Output)."

    command = [
        swipl_bin, "-q",
        "-s", "dips.pl",
        "-g", goal,
        "-t", "halt"
    ]

    try:
        result = subprocess.run(
            command,
            cwd=dips_dir,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        clean_stdout = result.stdout.strip()
        clean_stderr = result.stderr.strip()

        with open(output_text_file, 'w', encoding='utf-8') as f:
            f.write(f"TARGET:{target_str}\n")

            if clean_stderr and ("ERROR:" in clean_stderr or "Syntax error" in clean_stderr):
                f.write(f"ERROR:\n{clean_stderr}\n")
                return "PROLOG_ERROR"
            elif clean_stdout:
                f.write(clean_stdout + "\n")
                if clean_stdout == "false":
                    return "FALSE"
                return "SOLUTION"
            else:
                f.write("NO_OUTPUT\n")
                return "PROLOG_ERROR"

    except subprocess.TimeoutExpired:
        with open(output_text_file, 'w', encoding='utf-8') as f:
            f.write(f"TARGET:{target_str}\n")
            f.write("ERROR_TIMEOUT\n")
        return "TIMEOUT"

    except FileNotFoundError:
        with open(output_text_file, 'w', encoding='utf-8') as f:
            f.write(f"TARGET:{target_str}\n")
            f.write(f"ERROR_SWIPL_NOT_FOUND: Unable to execute '{swipl_bin}'. Verify the SWI-Prolog installation.\n")
        return "SWIPL_ERROR"


# ==============================================================================
# MAIN: EXECUTION ON ALL FOLDERS
# ==============================================================================
def main():
    print("=" * 70)
    print("🚀 DIPS EXECUTOR — Batch execution for all LLM outputs")
    print("=" * 70)

    # 1. Verify DIPS folder
    if not os.path.isdir(DIPS_DIR):
        print(f"❌ Error: DIPS folder not found at: {DIPS_DIR}")
        return

    file_dips_pl = os.path.join(DIPS_DIR, "dips.pl")
    if not os.path.isfile(file_dips_pl):
        print(f"❌ Error: dips.pl file not found at: {file_dips_pl}")
        return

    # 2. Detect SWI-Prolog executable
    swipl_bin = find_swipl_executable()
    print(f"📁 DIPS Folder       : {DIPS_DIR}")
    print(f"📂 Output Folder     : {OUTPUT_BASE_DIR}")
    print(f"⚙️ Prolog Executable : {swipl_bin}")
    print(f"⏱️ File Timeout      : {TIMEOUT_SECONDS}s")
    print("=" * 70)

    # 3. Find all folders with LLM files
    llm_folders = discover_llm_folders(BASE_DIR)

    if not llm_folders:
        print("⚠️ No folders with LLM output files found.")
        return

    print(f"\n🔍 Found {len(llm_folders)} model folders to process:")
    for model_name, (source_dir, file_list) in sorted(llm_folders.items()):
        print(f"  • {model_name:30s} : {len(file_list):3d} files (in {os.path.relpath(source_dir, BASE_DIR)})")

    # 4. Base output folder creation
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

    # 5. Execution for each folder / model
    overall_stats = {
        "total_files": 0,
        "solutions": 0,
        "false": 0,
        "prolog_errors": 0,
        "timeout": 0,
        "intent_errors": 0,
        "swipl_errors": 0
    }

    outcome_labels = {
        "SOLUTION": "✅ Solution found",
        "FALSE": "⚠️ false (no solution)",
        "PROLOG_ERROR": "❌ Prolog / Syntax Error",
        "TIMEOUT": "⏱️ Timeout exceeded",
        "INTENT_ERROR": "❌ Missing Intent ID",
        "SWIPL_ERROR": "❌ SWI-Prolog not found"
    }

    for model_index, (model_name, (source_dir, file_list)) in enumerate(sorted(llm_folders.items()), 1):
        # Dedicated folder for this model
        model_output_folder = os.path.join(OUTPUT_BASE_DIR, model_name)
        os.makedirs(model_output_folder, exist_ok=True)

        print(f"\n[{model_index}/{len(llm_folders)}] 📦 Processing: {model_name}")
        print(f"    Source   : {os.path.relpath(source_dir, BASE_DIR)}")
        print(f"    Output   : {os.path.relpath(model_output_folder, BASE_DIR)}")
        print(f"    Files    : {len(file_list)}")
        print("-" * 70)

        model_counts = {
            "SOLUTION": 0,
            "FALSE": 0,
            "PROLOG_ERROR": 0,
            "TIMEOUT": 0,
            "INTENT_ERROR": 0,
            "SWIPL_ERROR": 0
        }

        for idx, (filename, file_path) in enumerate(file_list, 1):
            output_text_file = os.path.join(model_output_folder, filename)
            
            outcome = execute_dips(
                dips_dir=DIPS_DIR,
                file_pl=file_path,
                output_text_file=output_text_file,
                swipl_bin=swipl_bin,
                timeout=TIMEOUT_SECONDS
            )

            model_counts[outcome] = model_counts.get(outcome, 0) + 1
            overall_stats["total_files"] += 1

            # Synthetic progress print
            outcome_description = outcome_labels.get(outcome, outcome)
            print(f"  [{idx:3d}/{len(file_list):3d}] {filename:<35s} -> {outcome_description}")

            # If swipl does not exist, interrupt to avoid 768 useless error messages
            if outcome == "SWIPL_ERROR":
                print(f"\n❌ CRITICAL ERROR: SWI-Prolog executable '{swipl_bin}' not found!")
                print("   Install SWI-Prolog or verify that 'swipl' is in the system PATH.")
                return

        # Global stats update
        overall_stats["solutions"] += model_counts["SOLUTION"]
        overall_stats["false"] += model_counts["FALSE"]
        overall_stats["prolog_errors"] += model_counts["PROLOG_ERROR"]
        overall_stats["timeout"] += model_counts["TIMEOUT"]
        overall_stats["intent_errors"] += model_counts["INTENT_ERROR"]

        # Model summary
        print(f"\n📊 Summary for {model_name}:")
        print(f"   Solutions found     : {model_counts['SOLUTION']:3d}")
        print(f"   False (no solution) : {model_counts['FALSE']:3d}")
        print(f"   Prolog errors       : {model_counts['PROLOG_ERROR']:3d}")
        print(f"   Timeouts            : {model_counts['TIMEOUT']:3d}")
        print(f"   Missing intents     : {model_counts['INTENT_ERROR']:3d}")

    # 6. Final global report
    print("\n" + "=" * 70)
    print("🏁 BATCH EXECUTION COMPLETED")
    print("=" * 70)
    print(f"Total files examined     : {overall_stats['total_files']}")
    print(f"Solutions found          : {overall_stats['solutions']}")
    print(f"False (no solution)      : {overall_stats['false']}")
    print(f"Prolog/Syntax errors     : {overall_stats['prolog_errors']}")
    print(f"Timeouts                 : {overall_stats['timeout']}")
    print(f"Missing Intent IDs       : {overall_stats['intent_errors']}")
    print(f"Results folder           : {OUTPUT_BASE_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()

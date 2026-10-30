import os
import sys
import json

# Import the VNF catalog parser
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, "../../../../../.."))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "scripts"))
# pyrefly: ignore [missing-import]
import catalog_parser

# Build the test JSON for a context-based split.
# Select a context range and include all three formulations (A, B, C).
# Each context produces three JSON records (one per schema).

# ============================================================
# CONFIGURATION: Modify these values to select the context range
# ============================================================
CONTEXT_START = 22   # First context to include (inclusive)
CONTEXT_END = 28     # Last context to include (inclusive)
# ============================================================

def main():
    base_dir = os.path.join(_PROJECT_ROOT, "dataset")
    output_dir = os.path.dirname(os.path.abspath(__file__))
    schemas = ["A", "B", "C"]

    if CONTEXT_START > CONTEXT_END:
        print(f"Error: CONTEXT_START ({CONTEXT_START}) must be <= CONTEXT_END ({CONTEXT_END}).")
        sys.exit(1)

    # We load the VNF map only once for efficiency
    catalog_json = os.path.join(base_dir, "catalogoVNF.json")
    try:
        vnf_map = catalog_parser.load_vnf_catalog(catalog_json)
        print(f"VNF catalog loaded: {len(vnf_map)} VNFs found.")
    except FileNotFoundError:
        print(f"Warning: VNF catalog not found in {catalog_json}. Text will not be enriched.")
        vnf_map = {}

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Creating test file for contexts from {CONTEXT_START} to {CONTEXT_END}...")
    print(f"For each context, all 3 schemas will be included: A, B, C")

    intents = []
    context_count = 0

    for i in range(CONTEXT_START, CONTEXT_END + 1):
        context_name = f"context{i}"
        context_path = os.path.join(base_dir, context_name)

        if not os.path.exists(context_path):
            print(f"  [SKIP] {context_name} - folder not found.")
            continue

        if not os.path.isdir(context_path):
            print(f"  [SKIP] {context_name} - is not a directory.")
            continue

        context_count += 1

        for schema in schemas:
            intent_filename = f"intent{schema}.txt"
            intent_path = os.path.join(context_path, intent_filename)

            if os.path.exists(intent_path):
                with open(intent_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()

                # Enrich the text with the hardware values of the VNF catalog
                if vnf_map:
                    content = catalog_parser.enrich_intent_with_hardware(content, vnf_map)

                intents.append({
                    "id": f"{context_name}_intent{schema}",
                    "input": content
                })
            else:
                print(f"  [WARN] {context_name}/{intent_filename} not found.")

    output_file = os.path.join(output_dir, f"test_context{CONTEXT_START}-{CONTEXT_END}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(intents, f, indent=4, ensure_ascii=False)

    print(f"\n[OK] Created {output_file}")
    print(f"     Processed contexts: {context_count} (from context{CONTEXT_START} to context{CONTEXT_END})")
    print(f"     Total intents: {len(intents)} (3 schemas x {context_count} contexts)")

if __name__ == "__main__":
    main()


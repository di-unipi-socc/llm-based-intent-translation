import os
import sys
import json

# Import the VNF catalog parser
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, "../../../../../.."))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "scripts"))
# pyrefly: ignore [missing-import]
import catalog_parser

# Program that creates a dataset in JSONL format for the context-level train/test split.
# Selects TWO distinct ranges of contexts and for each includes all 3 schemas (A, B, C).
# Each context produces 3 rows in JSONL (one per schema).

# ============================================================
# CONFIGURATION: Modify these values to select the two context ranges
# ============================================================
# First range
CONTEXT_START_1 = 1     # Number of the first context of the first range (included)
CONTEXT_END_1 = 7      # Number of the last context of the first range (included)

# Second range
CONTEXT_START_2 = 15    # Number of the first context of the second range (included)
CONTEXT_END_2 = 34      # Number of the last context of the second range (included)
# ============================================================

def main():
    INSTRUCTION = """Translate the natural language network intent into formal Prolog facts using the strictly defined schema below.

CRITICAL LOGIC RULES (MUST FOLLOW STEP-BY-STEP):

1. VNF Chain Identification & Grounding:
   - First, identify the exact chain of network functions (VNFs) explicitly requested in the input text.
   - This VNF chain constitutes the list of VNFs inside the 'target' fact (e.g., target(ServiceName, [vnf1, vnf2, ...])).
   - For all subsequent Prolog facts (vnf, vnfXUser, propertyExpectation), you MUST USE ONLY the VNFs from this exact target list. DO NOT invent, hallucinate, or mix up VNFs from other examples or contexts.

2. HARD vs SOFT Mapping (Non-Changing Properties):
   - Mandatory words: "must", "strictly", "required", "guaranteeing", "ensuring", "mandatory" -> Map to 'hard'.
   - Preference words: "prefer", "optimally", "should", "desired", "if possible" -> Map to 'soft'.

3. BEFORE vs AFTER Mapping (Changing Properties):
   - Topology depends on the preposition in the natural language:
   - If "[Service] AFTER [VnfID]": Source is VnfID, Destination is '_'.
     Template: propertyExpectation(PropID, IntentID, Type, _, VnfID, _).
   - If "[Service] BEFORE [VnfID]": Source is '_', Destination is VnfID.
     Template: propertyExpectation(PropID, IntentID, Type, _, _, VnfID).
   
SCHEMA DEFINITIONS:

1. Intent & Target:
   - intent(IntentID, ProviderOp, NumUsers, ServiceName). (IntentID ends in 'Intent', ProviderOp in 'Op').
   - target(ServiceName, [vnf1, vnf2, ...]).

2. Nodes (Hardware & Computing):
   - vnf(VnfID, edge/cloud, HardwareValue).
   - vnfXUser(VnfID, l, (1, NumUsers), ComputingValue).

3. Non-Changing Properties (9 params):
   - propertyExpectation(PropID, IntentID, Type, Operator, hard/soft, Value, Unit, SourceVNF, DestVNF).
   - Valid Types: bandwidth, latency, totChainHW, affinity. (Affinity Values: bound, dedicated, same).

4. Changing Properties (6 params):
   - propertyExpectation(PropID, IntentID, Type, _, Source, Destination).
   - Valid Types: security, compression, logging, privacy, caching, decoding, encoding.
"""

    dataset_dir = os.path.join(_PROJECT_ROOT, "dataset")
    output_dir = os.path.dirname(os.path.abspath(__file__))
    facts_filename = "facts.pl"
    schemas = ["intentA.txt", "intentB.txt", "intentC.txt"]

    # Range validation
    if CONTEXT_START_1 > CONTEXT_END_1:
        print(f"Error: CONTEXT_START_1 ({CONTEXT_START_1}) must be <= CONTEXT_END_1 ({CONTEXT_END_1}).")
        sys.exit(1)
    if CONTEXT_START_2 > CONTEXT_END_2:
        print(f"Error: CONTEXT_START_2 ({CONTEXT_START_2}) must be <= CONTEXT_END_2 ({CONTEXT_END_2}).")
        sys.exit(1)

    # We load the VNF map only once for efficiency
    catalog_json = os.path.join(dataset_dir, "catalogoVNF.json")
    try:
        vnf_map = catalog_parser.load_vnf_catalog(catalog_json)
        print(f"VNF catalog loaded: {len(vnf_map)} VNFs found.")
    except FileNotFoundError:
        print(f"Warning: VNF catalog not found in {catalog_json}. Text will not be enriched.")
        vnf_map = {}

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Build the context list from the two ranges
    selected_contexts = list(range(CONTEXT_START_1, CONTEXT_END_1 + 1)) + \
                             list(range(CONTEXT_START_2, CONTEXT_END_2 + 1))

    training_jsonl_file = os.path.join(
        output_dir,
        f"dataset_train_context{CONTEXT_START_1}-{CONTEXT_END_1}_{CONTEXT_START_2}-{CONTEXT_END_2}.jsonl"
    )

    print(f"Training dataset creation for two context ranges:")
    print(f"  Range 1: context{CONTEXT_START_1} - context{CONTEXT_END_1}")
    print(f"  Range 2: context{CONTEXT_START_2} - context{CONTEXT_END_2}")
    print(f"For each context, all 3 schemas will be included: A, B, C")

    with open(training_jsonl_file, "w", encoding="utf-8") as output_file_handle:
        count = 0
        context_count = 0

        for i in selected_contexts:
            folder_name = f"context{i}"
            folder_path = os.path.join(dataset_dir, folder_name)
            prolog_path = os.path.join(folder_path, facts_filename)

            if not os.path.exists(folder_path):
                print(f"  [SKIP] {folder_name} - folder not found.")
                continue

            if not os.path.exists(prolog_path):
                print(f"  [SKIP] {folder_name} - {facts_filename} not found.")
                continue

            with open(prolog_path, "r", encoding="utf-8") as prolog_file:
                prolog_code = prolog_file.read().strip()

            context_count += 1

            for text_filename in schemas:
                text_path = os.path.join(folder_path, text_filename)

                if os.path.exists(text_path):
                    with open(text_path, "r", encoding="utf-8") as text_file:
                        natural_language_text = text_file.read().strip()

                    # Enrich the text with the hardware values of the VNF catalog
                    if vnf_map:
                        natural_language_text = catalog_parser.enrich_intent_with_hardware(natural_language_text, vnf_map)

                    json_record = {
                        "instruction": INSTRUCTION,
                        "input": natural_language_text,
                        "output": prolog_code
                    }

                    output_file_handle.write(json.dumps(json_record, ensure_ascii=False) + "\n")
                    count += 1
                else:
                    print(f"  [WARN] {folder_name}/{text_filename} not found.")

    print(f"\n[OK] Created {training_jsonl_file}")
    print(f"     Processed contexts: {context_count}")
    print(f"       Range 1: context{CONTEXT_START_1}-{CONTEXT_END_1}")
    print(f"       Range 2: context{CONTEXT_START_2}-{CONTEXT_END_2}")
    print(f"     Total rows: {count} (3 schemas x {context_count} contexts)")

if __name__ == "__main__":
    main()


from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import torch
import json
import os
import time
from datetime import datetime


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

    # System instruction (must be identical to the one used in train_qwen.py)
    SYSTEM_PROMPT = """Translate the natural language network intent into formal Prolog facts using the strictly defined schema below.

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

    # --- PHASE 1: LOADING THE TRAINED MODEL ---
    # MODIFY HERE: insert the path of the trained model folder
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = os.path.normpath(os.path.join(script_dir, 'qwen2.5-7b-1-28')),
        max_seq_length = 2048,
        load_in_4bit = False,
    )

    # Apply the same chat template used during training
    tokenizer = get_chat_template(
        tokenizer,
        chat_template = "qwen-2.5",
    )

    FastLanguageModel.for_inference(model)  # Optimize the model for inference

    # --- PHASE 2: LOADING THE JSON FILE WITH REQUESTS ---
    # MODIFY HERE: insert the path of the test JSON file
    json_path = os.path.normpath(os.path.join(script_dir, 'test_context29-34.json'))
    output_folder = os.path.normpath(os.path.join(script_dir, '../result'))

    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            requests = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{json_path}' was not found.")
        requests = []

    print(f"Found {len(requests)} requests to process.")

    # Dictionary to collect execution times
    execution_times = {}

    # --- PHASE 3: PROCESSING EACH REQUEST ---
    for i, item in enumerate(requests):
        # Handles both a list of strings and a list of JSON dictionaries
        if isinstance(item, dict):
            request_text = item.get("input", item.get("richiesta", item.get("text", str(item))))
            filename = f"output_{item.get('id', i+1)}.txt"
        else:
            request_text = str(item)
            filename = f"output_{i+1}.txt"

        print(f"[{i+1}/{len(requests)}] Processing request in progress...")

        # Measure inference execution time
        start_timestamp = datetime.now()
        start_time = time.time()

        # Build the conversation in the native chat format of Qwen 2.5
        conversation = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": request_text},
        ]

        # Apply the chat template and tokenize
        prompt = tokenizer.apply_chat_template(
            conversation,
            tokenize = False,
            add_generation_prompt = True,  # Adds <|im_start|>assistant\n to start generation
        )

        inputs = tokenizer(
            [prompt],
            return_tensors = "pt",
        ).to("cuda")

        # Generate the response
        outputs = model.generate(**inputs, max_new_tokens = 2048)
        response_text = tokenizer.batch_decode(outputs, skip_special_tokens=True)

        # End time measurement
        end_time = time.time()
        end_timestamp = datetime.now()
        duration_seconds = round(end_time - start_time, 4)

        # Clean the response: extract only the last assistant message
        try:
            # With the Qwen 2.5 format, the assistant's response follows the last "assistant\n"
            full_response = response_text[0]
            # Look for the last occurrence of the assistant role in the decoded text
            path_parts = full_response.rsplit("assistant\n", 1)
            if len(path_parts) > 1:
                clean_response = path_parts[-1].strip()
            else:
                # Fallback: let's try with the Alpaca format just in case
                clean_response = full_response.split("### Response:")[-1].strip()
        except (IndexError, AttributeError):
            clean_response = response_text[0].strip()  # Generic fallback

        # --- PHASE 4: SAVING IN A SEPARATE TXT FILE ---
        save_path = os.path.join(output_folder, filename)
        with open(save_path, "w", encoding="utf-8") as output_file_handle:
            output_file_handle.write(clean_response)

        # Save the execution time for this file
        execution_times[filename] = {
            "durata_secondi": duration_seconds,
            "timestamp_inizio": start_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_fine": end_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }
        print(f"    Execution time: {duration_seconds:.4f}s")

    # --- PHASE 5: SAVING EXECUTION TIMES FILE ---
    timing_path = os.path.join(output_folder, "tempi_esecuzione.json")
    with open(timing_path, "w", encoding="utf-8") as timing_file:
        json.dump(execution_times, timing_file, indent=2, ensure_ascii=False)

    print(f"\nProcessing completed. All results have been saved in '{output_folder}/'.")
    print(f"Execution times file saved in: {timing_path}")


if __name__ == "__main__":
    main()

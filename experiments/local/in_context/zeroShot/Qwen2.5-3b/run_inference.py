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
    SYSTEM_PROMPT = """ROLE AND OBJECTIVE
You are an expert networking logic parser. Your task is to extract information from a natural language network intent and translate it into formal Prolog facts using ONLY the strictly defined schema below. You must not hallucinate, invent, or assume any information outside the provided text.


STEP 1: VNF CHAIN IDENTIFICATION & GROUNDING
- Identify the exact chain of Virtual Network Functions (VNFs) explicitly requested in the input text.
- This VNF chain constitutes the list of VNFs inside the target fact:
  target(ServiceName, [vnf1, vnf2, ...]).
- CRITICAL: For all subsequent Prolog facts (vnf, vnfXUser, propertyExpectation), you MUST USE ONLY the VNFs from this exact target list.


STEP 2: VOCABULARY AND KEYWORD MAPPING

Strictness Mapping:
- "must", "strictly", "required", "guaranteeing", "ensuring", "mandatory" -> hard
- "prefer", "optimally", "should", "desired", "if possible" -> soft

Operator Mapping:
- "greater than", "higher than", "above" -> greater
- "lower than", "below", "less than" -> lower

Unit Mapping:
- "Mbps", "megabps" -> megabps
- "ms", "milliseconds" -> ms
- "GB", "gigabytes" -> gb


STEP 3: TOPOLOGY AND PROPERTY MAPPING (BEFORE vs AFTER)
When mapping Changing Properties (like security, decoding, etc.), topology depends on the preposition in the text.
Use the underscore "_" to denote an empty or unspecified argument.

- AFTER Rule:
  If "[Service] AFTER [VnfID]", Source is VnfID and Destination is "_".
  Template: propertyExpectation(PropID, IntentID, Type, _, VnfID, _).

- BEFORE Rule:
  If "[Service] BEFORE [VnfID]", Source is "_" and Destination is VnfID.
  Template: propertyExpectation(PropID, IntentID, Type, _, _, VnfID).


STEP 4: STRICT PROLOG SCHEMA DEFINITIONS
Generate the output using EXACTLY these formats. Do not add extra parameters. Note on PropIDs: You must invent unique identifiers for each PropID (e.g., prop1, prop2, prop3). These identifiers have no semantic meaning in the results, but they must be strictly unique within your generated response.

1. Intent & Target:
- intent(IntentID, ProviderOp, NumUsers, ServiceName).
  (Note: IntentID must end in 'Intent', ProviderOp in 'Op')
- target(ServiceName, [vnf1, vnf2, ...]).

2. Nodes (Hardware & Computing):
- vnf(VnfID, edge/cloud, HardwareValue).
- vnfXUser(VnfID, l, (1, NumUsers), HardwareValue).

3. Non-Changing Properties (Expects EXACTLY 9 parameters):
- Template: propertyExpectation(PropID, IntentID, Type, Operator, hard/soft, Value, Unit, SourceVNF, DestVNF).
- Valid Types: bandwidth, latency, totChainHW, affinity
- Affinity Values: dedicated, same
- Note: For affinity and totChainHW, use "_" for Operator, Value, Unit, Source, or Dest where not applicable.

4. Changing Properties (Expects EXACTLY 6 parameters):
- Template: propertyExpectation(PropID, IntentID, Type, _, Source, Destination).
- Note: The 4th parameter is ALWAYS "_".
- Valid Types: security, compression, logging, privacy, caching, decoding, encoding


FINAL OUTPUT INSTRUCTION
Return ONLY the generated Prolog facts.
Do not include introductory text, conversational filler, or explanations.
"""

    # --- PHASE 1: LOADING THE TRAINED MODEL ---
    # MODIFY HERE: insert the path of the trained model folder
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = "unsloth/Qwen2.5-Coder-3B-Instruct",
        max_seq_length = 8192,
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
    json_path = os.path.normpath(os.path.join(script_dir, 'test_context1-34.json'))
    output_folder = os.path.normpath(os.path.join(script_dir, './result'))

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
        outputs = model.generate(**inputs, max_new_tokens = 8192)
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

import os
import json
import time
from datetime import datetime
# pyrefly: ignore [missing-import]
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable



API_KEY = os.getenv("GEMINI_API_KEY", "") # insert Gemini key here

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

# Gemini model initialization

# ==========================================
# 2. API CALL FUNCTION WITH RETRY
# ==========================================
def call_gemini_with_retry(model, user_prompt, max_retries=5):
    """
    Automatically handles rate limits (429) and server unavailability (503).
    """
    wait_seconds = 60
    
    for attempt in range(1, max_retries + 1):
        try:
            response = model.generate_content(user_prompt)
            
            # Safety pause of 5 seconds
            time.sleep(5) 
            
            return response.text.strip() if response.text else ""

        except (ResourceExhausted, ServiceUnavailable) as e:
            print(f"\n⚠️ [Attempt {attempt}/{max_retries}] API Error: {type(e).__name__}")
            print(f"   Quota exceeded or server busy. Pausing for {wait_seconds}s...")
            time.sleep(wait_seconds)
            
        except Exception as e:
            error_message = str(e)
            if "429" in error_message or "503" in error_message or "RESOURCE_EXHAUSTED" in error_message:
                print(f"\n⚠️ [Attempt {attempt}/{max_retries}] Quota/service block.")
                print(f"   Pausing for {wait_seconds}s...")
                time.sleep(wait_seconds)
            else:
                print(f"\n❌ Critical error: {e}")
                raise e

    raise Exception(f"Unable to complete request after {max_retries} attempts.")

# ==========================================
# 3. JSON READING AND TXT SAVING
# ==========================================
def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(model_name="gemini-3.5-flash", system_instruction=SYSTEM_PROMPT)
    input_json_file = os.path.normpath(os.path.join(script_dir, 'test_context1-34.json'))  # Insert here the name of your JSON file
    output_folder = os.path.normpath(os.path.join(script_dir, 'result_3.5-flash'))
    
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    if not os.path.exists(input_json_file):
        print(f"❌ Error: The input file '{input_json_file}' was not found.")
        return

    # Load data from the JSON file
    with open(input_json_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    total = len(dataset)
    print(f"Starting baseline test on {total} requests extracted from JSON...\n")

    # Dictionary to accumulate execution times
    timing_json_path = os.path.join(output_folder, "tempi_esecuzione.json")

    # Load already existing times (append) if the file exists
    if os.path.exists(timing_json_path):
        with open(timing_json_path, "r", encoding="utf-8") as timing_file:
            execution_times = json.load(timing_file)
        print(f"📂 Loaded {len(execution_times)} existing times from '{timing_json_path}'.")
    else:
        execution_times = {}

    for idx, item in enumerate(dataset, 1):
        # Extracts ID and input text from JSON
        request_id = item.get("id", f"unknown_{idx}")
        intent_text = item.get("input", "")
        
        if not intent_text:
            print(f"[{idx}/{total}] ⚠️ No input found for ID '{request_id}', skipping.")
            continue

        print(f"[{idx}/{total}] Interrogating Gemini for: {request_id}.txt")

        try:
            # Timestamp BEFORE the API call
            start_timestamp = datetime.now()
            t_start = time.time()

            # API call with Rate Limit management
            generated_prolog = call_gemini_with_retry(model, intent_text)

            # Timestamp AFTER receiving the response
            t_end = time.time()
            end_timestamp = datetime.now()
            duration_seconds = round(t_end - t_start, 4)

            # Create the file name using the "id" field
            filename = f"{request_id}.txt"
            file_path = os.path.join(output_folder, filename)

            # Save the result generated by Gemini in the txt file
            with open(file_path, "w", encoding="utf-8") as output_file_handle:
                output_file_handle.write(generated_prolog)

            # Record execution times
            execution_times[filename] = {
                "durata_secondi": duration_seconds,
                "timestamp_inizio": start_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp_fine": end_timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }

            # Save the times JSON incrementally (at each iteration)
            with open(timing_json_path, "w", encoding="utf-8") as timing_file:
                json.dump(execution_times, timing_file, indent=2, ensure_ascii=False)

            print(f"   ⏱️ Response time: {duration_seconds}s")

        except Exception as e:
            print(f"❌ Unable to process item {request_id}: {e}")

    print(f"\n✅ Test completed! The {total} .txt files have been saved in the '{output_folder}' folder.")
    print(f"📊 Execution times saved in: {timing_json_path}")

if __name__ == "__main__":
    main()
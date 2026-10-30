import os
import json
import time
from datetime import datetime
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

EXAMPLES

1)

INPUT:
The financial provider fraudSafeOp requires an antifraud analysis service to manage 200,000 transactions per hour. This system intercepts every digital payment request, compares it with habitual user spending patterns via machine learning, and authorizes the transaction in a few milliseconds. The deployed service chain includes, in order: a <requestInterceptorVF, 8> at the edge, a <profileMatcherVF, 16> at the edge, an <mlAnalyzerVF, 32> in the cloud, a <policyEnforcerVF, 12> in the cloud, and a <responseEmitterVF, 8> in the cloud. Regarding requirements, security is applied after the <requestInterceptorVF, 8>. Furthermore, it is strictly required that the <requestInterceptorVF, 8> and the <profileMatcherVF, 16> are deployed on the same hosting node. Privacy is executed before the <mlAnalyzerVF, 32>. Finally, the provider prefers that the bandwidth from the <mlAnalyzerVF, 32> to the <policyEnforcerVF, 12> remains higher than 1000 Mbps, and that the total chain hardware remains lower than 120 GB.

OUTPUT:
intent(fraudDetectionIntent, fraudSafeOp, 200000, fraudDetectionService).


propertyExpectation(affReq, fraudDetectionIntent, affinity, same, hard, _, _, requestInterceptorVF, profileMatcherVF).
propertyExpectation(bwReq, fraudDetectionIntent, bandwidth, greater, soft, 1000, megabps, mlAnalyzerVF, policyEnforcerVF).
propertyExpectation(hwReq, fraudDetectionIntent, totChainHW, lower, soft, 120, gb, _, _).

propertyExpectation(secReq, fraudDetectionIntent, security, _, requestInterceptorVF, _).
propertyExpectation(privReq, fraudDetectionIntent, privacy, _, _, mlAnalyzerVF).

target(fraudDetectionService, [requestInterceptorVF, profileMatcherVF, mlAnalyzerVF, policyEnforcerVF, responseEmitterVF]).

vnf(requestInterceptorVF, edge, 8).
vnf(profileMatcherVF, edge, 16).
vnf(mlAnalyzerVF, cloud, 32).
vnf(policyEnforcerVF, cloud, 12).
vnf(responseEmitterVF, cloud, 8).

vnfXUser(requestInterceptorVF, l, (1, 200000), 8).
vnfXUser(profileMatcherVF, l, (1, 200000), 16).
vnfXUser(mlAnalyzerVF, l, (1, 200000), 32).
vnfXUser(policyEnforcerVF, l, (1, 200000), 12).
vnfXUser(responseEmitterVF, l, (1, 200000), 8).


2)

INPUT:
The healthcare provider medDiagnosticOp requires a radiology AI diagnostics service to manage 10,000 daily scans. This pipeline receives high-resolution medical images, processes them with computer vision algorithms to highlight suspicious lesions, and stores them securely. The service chain begins with a <dicomIngesterVF, 16> allocated at the edge, specifying compression is applied after it. The chain then connects to a <lesionAnalyzerVF, 32> located in the cloud and a <metadataExtractorVF, 12> located in the cloud; for these two components, it is mandatory that they are isolated on dedicated hardware nodes, while ensuring the bandwidth from the <dicomIngesterVF, 16> to the <lesionAnalyzerVF, 32> remains higher than 500 Mbps. Finally, the system routes the data to a secure <secureArchiverVF, 24> in the cloud, ensuring that data encoding is executed before it.

OUTPUT:
intent(radiologyAIIntent, medDiagnosticOp, 10000, radiologyPipelineService).

propertyExpectation(affReq, radiologyAIIntent, affinity, dedicated, hard, _, _, lesionAnalyzerVF, _).
propertyExpectation(affReq, radiologyAIIntent, affinity, dedicated, hard, _, _, metadataExtractorVF, _).
propertyExpectation(bwReq, radiologyAIIntent, bandwidth, greater, hard, 500, megabps, dicomIngesterVF, lesionAnalyzerVF).

propertyExpectation(compReq, radiologyAIIntent, compression, _, dicomIngesterVF, _).
propertyExpectation(encReq, radiologyAIIntent, encoding, _, _, secureArchiverVF).

target(radiologyPipelineService, [dicomIngesterVF, lesionAnalyzerVF, metadataExtractorVF, secureArchiverVF]).

vnf(dicomIngesterVF, edge, 16).
vnf(lesionAnalyzerVF, cloud, 32).
vnf(metadataExtractorVF, cloud, 12).
vnf(secureArchiverVF, cloud, 24).

vnfXUser(dicomIngesterVF, l, (1, 10000), 16).
vnfXUser(lesionAnalyzerVF, l, (1, 10000), 32).
vnfXUser(metadataExtractorVF, l, (1, 10000), 12).
vnfXUser(secureArchiverVF, l, (1, 10000), 24).

3)

INPUT:
The financial provider onlineBankOp requires a digital identity verification service to manage 10,000 daily uploads. This service processes photos of documents uploaded by users, verifies their authenticity, and compares the data with international blacklists to prevent money laundering. Specifying that encoding is applied after the initial receiving function, the service begins with a <documentReceiverVF, 12> allocated at the edge. Ensuring that security is executed before the second phase, the chain connects to an <authenticityCheckerVF, 24> located in the cloud. Specifying that privacy is applied after the <amlMatcherVF, 16>, the chain incorporates an <amlMatcherVF, 16> located in the cloud. Finally, ensuring that compression is executed before the final node, the system completes the pipeline with a <profileCreatorVF, 16> located in the cloud.

OUTPUT:
intent(kycVerificationIntent, onlineBankOp, 10000, digitalIdentityService).

propertyExpectation(encReq, kycVerificationIntent, encoding, _, documentReceiverVF, _).
propertyExpectation(secReq, kycVerificationIntent, security, _, _, authenticityCheckerVF).
propertyExpectation(privReq, kycVerificationIntent, privacy, _, amlMatcherVF, _).
propertyExpectation(compReq, kycVerificationIntent, compression, _, _, profileCreatorVF).

target(digitalIdentityService, [documentReceiverVF, authenticityCheckerVF, amlMatcherVF, profileCreatorVF]).

vnf(documentReceiverVF, edge, 12).
vnf(authenticityCheckerVF, cloud, 24).
vnf(amlMatcherVF, cloud, 16).
vnf(profileCreatorVF, cloud, 16).

vnfXUser(documentReceiverVF, l, (1, 10000), 12).
vnfXUser(authenticityCheckerVF, l, (1, 10000), 24).
vnfXUser(amlMatcherVF, l, (1, 10000), 16).
vnfXUser(profileCreatorVF, l, (1, 10000), 16).


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
    output_folder = os.path.normpath(os.path.join(script_dir, 'result_3.5-flash-3'))
    
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
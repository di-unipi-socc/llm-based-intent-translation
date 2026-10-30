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

4)

INPUT:
The municipal provider smartParkOp requires a parking management backend to handle 100,000 active parking spots. This system receives occupancy alerts, updates the city map, and processes automatic payments. The service chain includes, in order: a <sensorDataCollectorVF, 8> at the edge, a <mapUpdaterVF, 16> in the cloud, a <paymentProcessorVF, 24> in the cloud, a <statusLoggerVF, 12> in the cloud, and a <securityEnforcerVF, 16> in the cloud. Regarding requirements, compression is applied after the <sensorDataCollectorVF, 8>. Encoding is executed before the <paymentProcessorVF, 24>. Security is applied after the <paymentProcessorVF, 24>. Logging is executed before the <statusLoggerVF, 12>. Furthermore, it is mandatory that the <mapUpdaterVF, 16> and the <paymentProcessorVF, 24> are deployed on dedicated nodes. Finally, it is strictly required that the latency from the <sensorDataCollectorVF, 8> to the <securityEnforcerVF, 16> remains below 30 ms.

OUTPUT:
intent(smartParkingIntent, smartParkOp, 100000, smartParkingBackend).

propertyExpectation(affReq, smartParkingIntent, affinity, dedicated, hard, _, _, paymentProcessorVF, _).
propertyExpectation(affReq, smartParkingIntent, affinity, dedicated, hard, _, _, mapUpdaterVF, _).
propertyExpectation(latReq, smartParkingIntent, latency, lower, hard, 30, ms, sensorDataCollectorVF, securityEnforcerVF).

propertyExpectation(compReq, smartParkingIntent, compression, _, sensorDataCollectorVF, _).
propertyExpectation(encReq, smartParkingIntent, encoding, _, _, paymentProcessorVF).
propertyExpectation(secReq, smartParkingIntent, security, _, paymentProcessorVF, _).
propertyExpectation(logReq, smartParkingIntent, logging, _, _, statusLoggerVF).

target(smartParkingBackend, [sensorDataCollectorVF, mapUpdaterVF, paymentProcessorVF, statusLoggerVF, securityEnforcerVF]).

vnf(sensorDataCollectorVF, edge, 8).
vnf(mapUpdaterVF, cloud, 16).
vnf(paymentProcessorVF, cloud, 24).
vnf(statusLoggerVF, cloud, 12).
vnf(securityEnforcerVF, cloud, 16).

vnfXUser(sensorDataCollectorVF, l, (1, 100000), 8).
vnfXUser(mapUpdaterVF, l, (1, 100000), 16).
vnfXUser(paymentProcessorVF, l, (1, 100000), 24).
vnfXUser(statusLoggerVF, l, (1, 100000), 12).
vnfXUser(securityEnforcerVF, l, (1, 100000), 16).

5)

INPUT:
The educational provider eduCloudOp requires a virtual student lab platform to support 10,000 concurrent students. This system provides temporary programming environments, manages resource allocation for each student, and monitors the workspaces to prevent improper use. The service chain begins with a <sessionIngesterVF, 8> allocated at the edge, data privacy mechanisms are applied after it. The system then connects to a <resourceAllocatorVF, 16> located in the cloud, ensuring that the network capacity between the <sessionIngesterVF, 8> and this <resourceAllocatorVF, 16> supports more than 500 Mbps. The pipeline continues to an <activityMonitorVF, 24> located in the cloud, ensuring that security are executed before it, and that the latency time from the <sessionIngesterVF, 8> to this <activityMonitorVF, 24> is kept under 40 ms. The next blocks are a <userPrivacyEnforcerVF, 12> located in the cloud and an <auditLoggerVF, 12> located in the cloud, where logging are executed before the <auditLoggerVF, 12>. Finally, the system routes the results to an <outputPackagerVF, 16> located in the cloud, specifying that compression is applied after it. For the whole deployment, the provider prefers that the aggregate infrastructure footprint stays below 120 GB.
OUTPUT:
intent(virtualLabIntent, eduCloudOp, 10000, virtualLabService).

propertyExpectation(latReq, virtualLabIntent, latency, lower, hard, 40, ms, sessionIngesterVF, activityMonitorVF).
propertyExpectation(bwReq, virtualLabIntent, bandwidth, greater, hard, 500, megabps, sessionIngesterVF, resourceAllocatorVF).
propertyExpectation(hwReq, virtualLabIntent, totChainHW, lower, soft, 120, gb, _, _).

propertyExpectation(privReq, virtualLabIntent, privacy, _, sessionIngesterVF, _).
propertyExpectation(secReq, virtualLabIntent, security, _, _, activityMonitorVF).
propertyExpectation(logReq, virtualLabIntent, logging, _, _, auditLoggerVF).
propertyExpectation(compReq, virtualLabIntent, compression, _, outputPackagerVF, _).

target(virtualLabService, [sessionIngesterVF, resourceAllocatorVF, activityMonitorVF, userPrivacyEnforcerVF, auditLoggerVF, outputPackagerVF]).

vnf(sessionIngesterVF, edge, 8).
vnf(resourceAllocatorVF, cloud, 16).
vnf(activityMonitorVF, cloud, 24).
vnf(userPrivacyEnforcerVF, cloud, 12).
vnf(auditLoggerVF, cloud, 12).
vnf(outputPackagerVF, cloud, 16).

vnfXUser(sessionIngesterVF, l, (1, 10000), 8).
vnfXUser(resourceAllocatorVF, l, (1, 10000), 16).
vnfXUser(activityMonitorVF, l, (1, 10000), 24).
vnfXUser(userPrivacyEnforcerVF, l, (1, 10000), 12).
vnfXUser(auditLoggerVF, l, (1, 10000), 12).
vnfXUser(outputPackagerVF, l, (1, 10000), 16).


6)

INPUT:

The industrial provider factoryCloudOp requires an augmented reality back-end service to support 500 active smart glasses on the shop floor. This service sends visual technical instructions to workers' headsets, overlaying maintenance data on the framed machinery in real time. The deployed service chain includes, in order: an <arStreamReceiverVF, 12> allocated at the edge, an <arPoseEstimatorVF, 24> located in the cloud, a <dataOverlayEngineVF, 32> located in the cloud, and an <arStreamDispatcherVF, 16> located in the cloud. Regarding system performance, the provider requires that the network bandwidth from the initial node to the <arPoseEstimatorVF, 24> remains higher than 200 Mbps. To prevent any lag in the workers' field of view, it is strictly required that the end-to-end latency from the <arStreamReceiverVF, 12> to the final <arStreamDispatcherVF, 16> remains below 12 ms. To avoid computational interference, it is mandatory that <arPoseEstimatorVF, 24> and the <dataOverlayEngineVF, 32> are hosted on separate, completely dedicated physical servers. Finally, the provider prefers that the total chain hardware remains lower than 90 GB to control operational costs.

OUTPUT:

intent(arBackendIntent, factoryCloudOp, 500, arRenderingService).

propertyExpectation(latReq, arBackendIntent, latency, lower, hard, 12, ms, arStreamReceiverVF, arStreamDispatcherVF).
propertyExpectation(bwReq, arBackendIntent, bandwidth, greater, hard, 200, megabps, arStreamReceiverVF, arPoseEstimatorVF).
propertyExpectation(hwReq, arBackendIntent, totChainHW, lower, soft, 90, gb, _, _).
propertyExpectation(affReq, arBackendIntent, affinity, dedicated, hard, _, _, arPoseEstimatorVF, _).
propertyExpectation(affReq, arBackendIntent, affinity, dedicated, hard, _, _, dataOverlayEngineVF, _).

target(arRenderingService, [arStreamReceiverVF, arPoseEstimatorVF, dataOverlayEngineVF, arStreamDispatcherVF]).

vnf(arStreamReceiverVF, edge, 12).
vnf(arPoseEstimatorVF, cloud, 24).
vnf(dataOverlayEngineVF, cloud, 32).
vnf(arStreamDispatcherVF, cloud, 16).

vnfXUser(arStreamReceiverVF, l, (1, 500), 12).
vnfXUser(arPoseEstimatorVF, l, (1, 500), 24).
vnfXUser(dataOverlayEngineVF, l, (1, 500), 32).
vnfXUser(arStreamDispatcherVF, l, (1, 500), 16).


7)

INPUT:
The agvFleetOp provider intends to deploy the agvLogisticsBackend service to manage a fleet of 500 users. The system must manage robotic vehicles that navigate the warehouse shelves, communicating with each other and with the central server to continuously recalculate routes and optimize material picking. The processing pipeline consists of an <agvTelemetryCollectorVF, 6> located in the edge, followed by a <routeOptimizerVF, 20> located in the cloud, a <taskDispatcherVF, 16> located in the cloud, and terminating with a <centralFleetSyncVF, 12> in the cloud. Regarding service modifications, compression is strictly required after the <agvTelemetryCollectorVF, 6>, security must be inserted before <routeOptimizerVF, 20>, and logging is ideally applied before the <centralFleetSyncVF, 12>. For operational performance, a latency of less than 15 ms is strictly required between the <agvTelemetryCollectorVF, 6> and <routeOptimizerVF, 20>, and <routeOptimizerVF, 20> must run on a dedicated host. Finally, it is desired to maintain a bandwidth higher than 50 megabps between the <agvTelemetryCollectorVF, 6> and the <taskDispatcherVF, 16>.

OUTPUT:
intent(agvRoutingIntent, agvFleetOp, 500, agvLogisticsBackend).

propertyExpectation(latReq, agvRoutingIntent, latency, lower, hard, 15, ms, agvTelemetryCollectorVF, routeOptimizerVF).
propertyExpectation(bwReq, agvRoutingIntent, bandwidth, greater, soft, 50, megabps, agvTelemetryCollectorVF, taskDispatcherVF).
propertyExpectation(affReq, agvRoutingIntent, affinity, dedicated, hard, _, _, routeOptimizerVF, _).

propertyExpectation(compReq, agvRoutingIntent, compression, _, agvTelemetryCollectorVF, _).
propertyExpectation(secReq, agvRoutingIntent, security, _, _, routeOptimizerVF).
propertyExpectation(logReq, agvRoutingIntent, logging, _, _, centralFleetSyncVF).

target(agvLogisticsBackend, [agvTelemetryCollectorVF, routeOptimizerVF, taskDispatcherVF, centralFleetSyncVF]).

vnf(agvTelemetryCollectorVF, edge, 6).
vnf(routeOptimizerVF, cloud, 20).
vnf(taskDispatcherVF, cloud, 16).
vnf(centralFleetSyncVF, cloud, 12).

vnfXUser(agvTelemetryCollectorVF, l, (1, 500), 6).
vnfXUser(routeOptimizerVF, l, (1, 500), 20).
vnfXUser(taskDispatcherVF, l, (1, 500), 16).
vnfXUser(centralFleetSyncVF, l, (1, 500), 12).


8)

INPUT:
The steelIndustryOp provider intends to deploy the digitalTwinService to manage 1500 users. The service manages a digital twin of a blast furnace and requires continuous synchronization of physical parameters (pressure, temperature) with the 3D model hosted in the cloud to simulate thermal efficiency in real time. The chain begins with <sensorIngestVF, 4> allocated at the edge and <dataFilteringVF, 6> allocated at the edge, mandating data compression immediately after <sensorIngestVF, 4>. Next, the flow continues to <thermalSimVF, 20> located in the cloud, where data decoding is strictly necessary before <thermalSimVF, 20> and a latency lower than 20 ms is mandatory between <sensorIngestVF, 4> and <thermalSimVF, 20>. Finally, the service finishes at <model3dVF, 25> located in the cloud. It is desired to keep total chain hardware consumption below 80 GB.

OUTPUT:
intent(agvRoutingIntent, agvFleetOp, 500, agvLogisticsBackend).

propertyExpectation(latReq, agvRoutingIntent, latency, lower, hard, 15, ms, agvTelemetryCollectorVF, routeOptimizerVF).
propertyExpectation(bwReq, agvRoutingIntent, bandwidth, greater, soft, 50, megabps, agvTelemetryCollectorVF, taskDispatcherVF).
propertyExpectation(affReq, agvRoutingIntent, affinity, dedicated, hard, _, _, routeOptimizerVF, _).

propertyExpectation(compReq, agvRoutingIntent, compression, _, agvTelemetryCollectorVF, _).
propertyExpectation(secReq, agvRoutingIntent, security, _, _, routeOptimizerVF).
propertyExpectation(logReq, agvRoutingIntent, logging, _, _, centralFleetSyncVF).

target(agvLogisticsBackend, [agvTelemetryCollectorVF, routeOptimizerVF, taskDispatcherVF, centralFleetSyncVF]).

vnf(agvTelemetryCollectorVF, edge, 6).
vnf(routeOptimizerVF, cloud, 20).
vnf(taskDispatcherVF, cloud, 16).
vnf(centralFleetSyncVF, cloud, 12).

vnfXUser(agvTelemetryCollectorVF, l, (1, 500), 6).
vnfXUser(routeOptimizerVF, l, (1, 500), 20).
vnfXUser(taskDispatcherVF, l, (1, 500), 16).
vnfXUser(centralFleetSyncVF, l, (1, 500), 12).


9)
INPUT:

The logistics provider aeroDeliveryOp requires a drone fleet control service to manage 5,000 active delivery drones. This system manages digital flight plans, avoids software collisions, and ensures that the command signal is always a priority. Specifying that caching is applied after the initial function, the service begins with a <flightTelemetryIngesterVF, 12> ingester allocated at the edge. Mandating that the latency from this first component to the <collisionAvoiderVF, 32> remains below 10 ms, the chain connects to a <collisionAvoiderVF, 32> located in the cloud. Preferring that the total chain hardware remains lower than 200 GB, the chain incorporates a <commandPrioritizerVF, 16> located in the cloud. Finally, preferring that the bandwidth from the <collisionAvoiderVF, 32> to the final point remains higher than 2000 Mbps, the system completes the pipeline with a <routeDispatcherVF, 12> allocated at the edge.

OUTPUT:
intent(droneControlIntent, aeroDeliveryOp, 5000, droneFleetControlService).

propertyExpectation(hwReq, droneControlIntent, totChainHW, lower, soft, 200, gb, _, _).
propertyExpectation(latReq, droneControlIntent, latency, lower, hard, 10, ms, flightTelemetryIngesterVF, collisionAvoiderVF).
propertyExpectation(bwReq, droneControlIntent, bandwidth, greater, soft, 2000, megabps, collisionAvoiderVF, routeDispatcherVF).

propertyExpectation(cachReq, droneControlIntent, caching, _, flightTelemetryIngesterVF, _).

target(droneFleetControlService, [flightTelemetryIngesterVF, collisionAvoiderVF, commandPrioritizerVF, routeDispatcherVF]).

vnf(flightTelemetryIngesterVF, edge, 12).
vnf(collisionAvoiderVF, cloud, 32).
vnf(commandPrioritizerVF, cloud, 16).
vnf(routeDispatcherVF, edge, 12).

vnfXUser(flightTelemetryIngesterVF, l, (1, 5000), 12).
vnfXUser(collisionAvoiderVF, l, (1, 5000), 32).
vnfXUser(commandPrioritizerVF, l, (1, 5000), 16).
vnfXUser(routeDispatcherVF, l, (1, 5000), 12).


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

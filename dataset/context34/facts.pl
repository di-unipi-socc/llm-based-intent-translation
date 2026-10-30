intent(nightSurveillanceIntent, securityOp, 50, perimeterSurveillanceService).

propertyExpectation(cp1, nightSurveillanceIntent, caching, _, cameraIngestVF, _).
propertyExpectation(cp2, nightSurveillanceIntent, privacy, _, _, videoStorageVF).

propertyExpectation(bw1, nightSurveillanceIntent, bandwidth, greater, soft, 50, megabps, cameraIngestVF, intrusionDetectVF).
propertyExpectation(aff1, nightSurveillanceIntent, affinity, dedicated, hard, _, _, intrusionDetectVF, _).

target(perimeterSurveillanceService, [cameraIngestVF, intrusionDetectVF, alarmDispatcherVF, videoStorageVF]).

vnf(cameraIngestVF, edge, 4).
vnf(intrusionDetectVF, edge, 16).
vnf(alarmDispatcherVF, cloud, 8).
vnf(videoStorageVF, cloud, 32).

vnfXUser(cameraIngestVF, l, (1, 50), 4).
vnfXUser(intrusionDetectVF, l, (1, 50), 16).
vnfXUser(alarmDispatcherVF, l, (1, 50), 8).
vnfXUser(videoStorageVF, l, (1, 50), 32).
intent(arBackendIntent, factoryCloudOp, 500, arRenderingService).

propertyExpectation(latReq, arBackendIntent, latency, lower, hard, 100, ms, arStreamReceiverVF, arStreamDispatcherVF).
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
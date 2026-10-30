intent(multiCamIntent, mediaBroadcastOp, 30000, liveStreamingService).

propertyExpectation(bwReq, multiCamIntent, bandwidth, greater, hard, 5000, megabps, graphicInjectorVF, streamDistributorVF).
propertyExpectation(hwReq, multiCamIntent, totChainHW, lower, soft, 150, gb, _, _).

propertyExpectation(compReq, multiCamIntent, compression, _, streamIngesterVF, _).
propertyExpectation(cachReq, multiCamIntent, caching, _, _, streamDistributorVF).

target(liveStreamingService, [streamIngesterVF, cloudStudioVF, graphicInjectorVF, streamDistributorVF]).

vnf(streamIngesterVF, edge, 12).
vnf(cloudStudioVF, cloud, 32).
vnf(graphicInjectorVF, cloud, 16).
vnf(streamDistributorVF, cloud, 24).

vnfXUser(streamIngesterVF, l, (1, 30000), 12).
vnfXUser(cloudStudioVF, l, (1, 30000), 32).
vnfXUser(graphicInjectorVF, l, (1, 30000), 16).
vnfXUser(streamDistributorVF, l, (1, 30000), 24).
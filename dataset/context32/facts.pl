intent(thermalTwinIntent, steelIndustryOp, 1500, digitalTwinService).

propertyExpectation(cp1, thermalTwinIntent, compression, _, sensorIngestVF, _).
propertyExpectation(cp2, thermalTwinIntent, decoding, _, _, thermalSimVF).

propertyExpectation(lat1, thermalTwinIntent, latency, lower, hard, 35, ms, sensorIngestVF, thermalSimVF).
propertyExpectation(hw1, thermalTwinIntent, totChainHW, lower, soft, 80, gb, _, _).

target(digitalTwinService, [sensorIngestVF, dataFilteringVF, thermalSimVF, model3dVF]).

vnf(sensorIngestVF, edge, 4).
vnf(dataFilteringVF, edge, 6).
vnf(thermalSimVF, cloud, 20).
vnf(model3dVF, cloud, 25).


vnfXUser(sensorIngestVF, l, (1, 1500), 4).
vnfXUser(dataFilteringVF, l, (1, 1500), 6).
vnfXUser(thermalSimVF, l, (1, 1500), 20).
vnfXUser(model3dVF, l, (1, 1500), 25).


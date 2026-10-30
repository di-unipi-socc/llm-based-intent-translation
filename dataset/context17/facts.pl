intent(routeOptIntent, deliveryLogisticsOp, 15000, routeOptimizationService).

propertyExpectation(latReq, routeOptIntent, latency, lower, hard, 80, ms, gpsIngesterVF, terminalUpdaterVF).

propertyExpectation(compReq, routeOptIntent, compression, _, gpsIngesterVF, _).
propertyExpectation(decReq, routeOptIntent, decoding, _, _, terminalUpdaterVF).

target(routeOptimizationService, [gpsIngesterVF, trafficAnalyzerVF, routeOptimizerVF, terminalUpdaterVF]).

vnf(gpsIngesterVF, edge, 8).
vnf(trafficAnalyzerVF, cloud, 24).
vnf(routeOptimizerVF, cloud, 20).
vnf(terminalUpdaterVF, edge, 12).

vnfXUser(gpsIngesterVF, l, (1, 15000), 8).
vnfXUser(trafficAnalyzerVF, l, (1, 15000), 24).
vnfXUser(routeOptimizerVF, l, (1, 15000), 20).
vnfXUser(terminalUpdaterVF, l, (1, 15000), 12).
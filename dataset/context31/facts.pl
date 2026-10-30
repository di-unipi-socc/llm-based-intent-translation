intent(agvRoutingIntent, agvFleetOp, 500, agvLogisticsBackend).

propertyExpectation(latReq, agvRoutingIntent, latency, lower, hard, 30, ms, agvTelemetryCollectorVF, routeOptimizerVF).
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


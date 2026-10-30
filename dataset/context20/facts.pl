intent(telemetryMonitorIntent, serverMonOp, 50000, telemetryMonitoringService).

propertyExpectation(affReq, telemetryMonitorIntent, affinity, same, hard, _, _, telemetryCollectorVF, dataAggregatorVF).
propertyExpectation(latReq, telemetryMonitorIntent, latency, lower, hard, 100, ms, telemetryCollectorVF, alertDispatcherVF).
propertyExpectation(bwReq, telemetryMonitorIntent, bandwidth, greater, soft, 2000, megabps, telemetryCollectorVF, alertDispatcherVF).

target(telemetryMonitoringService, [telemetryCollectorVF, dataAggregatorVF, anomalyDetectorVF, alertDispatcherVF]).

vnf(telemetryCollectorVF, edge, 8).
vnf(dataAggregatorVF, edge, 16).
vnf(anomalyDetectorVF, cloud, 24).
vnf(alertDispatcherVF, cloud, 12).

vnfXUser(telemetryCollectorVF, l, (1, 50000), 8).
vnfXUser(dataAggregatorVF, l, (1, 50000), 16).
vnfXUser(anomalyDetectorVF, l, (1, 50000), 24).
vnfXUser(alertDispatcherVF, l, (1, 50000), 12).
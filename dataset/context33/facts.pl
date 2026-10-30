intent(oeeMonitoringIntent, smartFactoryOp, 300, oeeMonitoringService).

propertyExpectation(cp1, oeeMonitoringIntent, logging, _, machineIngestVF, _).
propertyExpectation(cp2, oeeMonitoringIntent, security, _, _, alertDispatcherVF).

propertyExpectation(lat1, oeeMonitoringIntent, latency, lower, hard, 15, ms, machineIngestVF, oeeAggregatorVF).
propertyExpectation(bw1, oeeMonitoringIntent, bandwidth, greater, soft, 20, megabps, oeeAggregatorVF, alertDispatcherVF).
propertyExpectation(aff1, oeeMonitoringIntent, affinity, dedicated, hard, _, _, alertDispatcherVF, _).

target(oeeMonitoringService, [machineIngestVF, oeeAggregatorVF, alertDispatcherVF, oeeAnalyticsVF]).

vnf(machineIngestVF, edge, 4).
vnf(oeeAggregatorVF, edge, 8).
vnf(alertDispatcherVF, cloud, 12).
vnf(oeeAnalyticsVF, cloud, 16).

vnfXUser(machineIngestVF, l, (1, 300), 4).
vnfXUser(oeeAggregatorVF, l, (1, 300), 8).
vnfXUser(alertDispatcherVF, l, (1, 300), 12).
vnfXUser(oeeAnalyticsVF, l, (1, 300), 16).


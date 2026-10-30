intent(smartParkingIntent, smartParkOp, 100000, smartParkingBackend).

propertyExpectation(affReq, smartParkingIntent, affinity, dedicated, hard, _, _, paymentProcessorVF, _).
propertyExpectation(affReq, smartParkingIntent, affinity, dedicated, hard, _, _, mapUpdaterVF, _).
propertyExpectation(latReq, smartParkingIntent, latency, lower, hard, 100, ms, sensorDataCollectorVF, securityEnforcerVF).

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
intent(cloudGamingIntent, cloudGamingOp, 40000, cloudGamingService).

propertyExpectation(latReq, cloudGamingIntent, latency, lower, hard, 30, ms, streamPackerVF, deliveryOptimizerVF).
propertyExpectation(affReq1, cloudGamingIntent, affinity, dedicated, soft, _, _, gameExecutorVF, _).
propertyExpectation(affReq2, cloudGamingIntent, affinity, dedicated, soft, _, _, streamPackerVF, _).

propertyExpectation(encReq, cloudGamingIntent, encoding, _, gameExecutorVF, _).

target(cloudGamingService, [gameExecutorVF, streamPackerVF, deliveryOptimizerVF]).

vnf(gameExecutorVF, cloud, 32).
vnf(streamPackerVF, cloud, 16).
vnf(deliveryOptimizerVF, edge, 8).

vnfXUser(gameExecutorVF, l, (1, 40000), 32).
vnfXUser(streamPackerVF, l, (1, 40000), 16).
vnfXUser(deliveryOptimizerVF, l, (1, 40000), 8).
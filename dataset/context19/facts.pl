intent(droneControlIntent, aeroDeliveryOp, 5000, droneFleetControlService).

propertyExpectation(hwReq, droneControlIntent, totChainHW, lower, soft, 200, gb, _, _).
propertyExpectation(latReq, droneControlIntent, latency, lower, hard, 50, ms, flightTelemetryIngesterVF, collisionAvoiderVF).
propertyExpectation(bwReq, droneControlIntent, bandwidth, greater, soft, 2000, megabps, collisionAvoiderVF, routeDispatcherVF).

propertyExpectation(cachReq, droneControlIntent, caching, _, flightTelemetryIngesterVF, _).

target(droneFleetControlService, [flightTelemetryIngesterVF, collisionAvoiderVF, commandPrioritizerVF, routeDispatcherVF]).

vnf(flightTelemetryIngesterVF, edge, 12).
vnf(collisionAvoiderVF, cloud, 32).
vnf(commandPrioritizerVF, cloud, 16).
vnf(routeDispatcherVF, edge, 12).

vnfXUser(flightTelemetryIngesterVF, l, (1, 5000), 12).
vnfXUser(collisionAvoiderVF, l, (1, 5000), 32).
vnfXUser(commandPrioritizerVF, l, (1, 5000), 16).
vnfXUser(routeDispatcherVF, l, (1, 5000), 12).
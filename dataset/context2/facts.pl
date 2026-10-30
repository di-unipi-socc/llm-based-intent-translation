intent(secureMailIntent, secureMailOp, 10000, emailSanitizationService).


propertyExpectation(latReq, secureMailIntent, latency, lower, soft, 50, ms, mailGatewayVF, phishingFilterVF).
propertyExpectation(bwReq, secureMailIntent, bandwidth, greater, hard, 100, megabps, phishingFilterVF, sandboxScannerVF).


propertyExpectation(decReq, secureMailIntent, decoding, _, mailGatewayVF, _).
propertyExpectation(logReq, secureMailIntent, logging, _, _, sandboxScannerVF).

target(emailSanitizationService, [mailGatewayVF, phishingFilterVF, sandboxScannerVF, safeDeliveryVF]).

vnf(mailGatewayVF, edge, 4).
vnf(phishingFilterVF, cloud, 8).
vnf(sandboxScannerVF, cloud, 16).
vnf(safeDeliveryVF, cloud, 4).

vnfXUser(mailGatewayVF, l, (1, 10000), 4).
vnfXUser(phishingFilterVF, l, (1, 10000), 8).
vnfXUser(sandboxScannerVF, l, (1, 10000), 16).
vnfXUser(safeDeliveryVF, l, (1, 10000), 4).
intent(antiDdosIntent, ddosProtectionOp, 50000, ddosMitigationService).

propertyExpectation(bwReq, antiDdosIntent, bandwidth, greater, hard, 500, megabps, networkTrafficAnalyzerVF, scrubbingFilterVF).
propertyExpectation(latReq, antiDdosIntent, latency, lower, soft, 30, ms, rateLimiterVF, webServerVF).

propertyExpectation(secReq, antiDdosIntent, security, _, _, scrubbingFilterVF).
propertyExpectation(logReq, antiDdosIntent, logging, _, rateLimiterVF, _).

target(ddosMitigationService, [networkTrafficAnalyzerVF, scrubbingFilterVF, rateLimiterVF, webServerVF]).

vnf(networkTrafficAnalyzerVF, edge, 8).
vnf(scrubbingFilterVF, cloud, 32).
vnf(rateLimiterVF, cloud, 16).
vnf(webServerVF, cloud, 12).

vnfXUser(networkTrafficAnalyzerVF, l, (1, 50000), 8).
vnfXUser(scrubbingFilterVF, l, (1, 50000), 32).
vnfXUser(rateLimiterVF, l, (1, 50000), 16).
vnfXUser(webServerVF, l, (1, 50000), 12).
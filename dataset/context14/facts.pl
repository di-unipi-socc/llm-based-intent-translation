intent(hftIntent, hftGlobalOp, 500000, highFrequencyTradingService).

propertyExpectation(latReq1, hftIntent, latency, lower, hard, 50, ms, marketFeedVF, tradingAlgoVF).
propertyExpectation(bwReq, hftIntent, bandwidth, greater, soft, 5000, megabps, tradingAlgoVF, riskCheckerVF).
propertyExpectation(latReq2, hftIntent, latency, lower, soft, 60, ms, riskCheckerVF, orderDispatcherVF).

propertyExpectation(cachReq, hftIntent, caching, _, marketFeedVF, _).
propertyExpectation(logReq, hftIntent, logging, _, _, orderDispatcherVF).

target(highFrequencyTradingService, [marketFeedVF, tradingAlgoVF, riskCheckerVF, orderDispatcherVF]).

vnf(marketFeedVF, edge, 16).
vnf(tradingAlgoVF, edge, 32).
vnf(riskCheckerVF, cloud, 16).
vnf(orderDispatcherVF, edge, 8).

vnfXUser(marketFeedVF, l, (1, 500000), 16).
vnfXUser(tradingAlgoVF, l, (1, 500000), 32).
vnfXUser(riskCheckerVF, l, (1, 500000), 16).
vnfXUser(orderDispatcherVF, l, (1, 500000), 8).
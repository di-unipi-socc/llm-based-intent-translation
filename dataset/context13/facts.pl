intent(fraudDetectionIntent, fraudSafeOp, 200000, fraudDetectionService).


propertyExpectation(affReq, fraudDetectionIntent, affinity, same, hard, _, _, requestInterceptorVF, profileMatcherVF).
propertyExpectation(bwReq, fraudDetectionIntent, bandwidth, greater, soft, 1000, megabps, mlAnalyzerVF, policyEnforcerVF).
propertyExpectation(hwReq, fraudDetectionIntent, totChainHW, lower, soft, 120, gb, _, _).

propertyExpectation(secReq, fraudDetectionIntent, security, _, requestInterceptorVF, _).
propertyExpectation(privReq, fraudDetectionIntent, privacy, _, _, mlAnalyzerVF).

target(fraudDetectionService, [requestInterceptorVF, profileMatcherVF, mlAnalyzerVF, policyEnforcerVF, responseEmitterVF]).

vnf(requestInterceptorVF, edge, 8).
vnf(profileMatcherVF, edge, 16).
vnf(mlAnalyzerVF, cloud, 32).
vnf(policyEnforcerVF, cloud, 12).
vnf(responseEmitterVF, cloud, 8).

vnfXUser(requestInterceptorVF, l, (1, 200000), 8).
vnfXUser(profileMatcherVF, l, (1, 200000), 16).
vnfXUser(mlAnalyzerVF, l, (1, 200000), 32).
vnfXUser(policyEnforcerVF, l, (1, 200000), 12).
vnfXUser(responseEmitterVF, l, (1, 200000), 8).
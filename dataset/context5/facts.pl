intent(encryptedTrafficIntent, secureCryptoOp, 25000, cryptoAnalysisService).

propertyExpectation(affReq, encryptedTrafficIntent, affinity, same, hard, _, _, trafficSplitterVF, featureExtractorVF).
propertyExpectation(hwReq, encryptedTrafficIntent, totChainHW, lower, soft, 80, gb, _, _).

propertyExpectation(decReq, encryptedTrafficIntent, decoding, _, trafficSplitterVF, _).
propertyExpectation(secReq, encryptedTrafficIntent, security, _, _, policyEnforcerVF).

target(cryptoAnalysisService, [trafficSplitterVF, featureExtractorVF, aiClassifierVF, alertManagerVF, policyEnforcerVF]).

vnf(trafficSplitterVF, edge, 8).
vnf(featureExtractorVF, edge, 16).
vnf(aiClassifierVF, cloud, 32).
vnf(alertManagerVF, cloud, 4).
vnf(policyEnforcerVF, cloud, 12).

vnfXUser(trafficSplitterVF, l, (1, 25000), 8).
vnfXUser(featureExtractorVF, l, (1, 25000), 16).
vnfXUser(aiClassifierVF, l, (1, 25000), 32).
vnfXUser(alertManagerVF, l, (1, 25000), 4).
vnfXUser(policyEnforcerVF, l, (1, 25000), 12).
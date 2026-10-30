intent(sentimentAnalysisIntent, sentimentOp, 100000, sentimentAnalysisService).

propertyExpectation(affReq, sentimentAnalysisIntent, affinity, same, hard, _, _, sentimentAnalyzerVF, reportDispatcherVF).

propertyExpectation(privReq, sentimentAnalysisIntent, privacy, _, socialDataReceiverVF, _).
propertyExpectation(secReq, sentimentAnalysisIntent, security, _, _, sentimentAnalyzerVF).

target(sentimentAnalysisService, [socialDataReceiverVF, sentimentAnalyzerVF, reportDispatcherVF]).

vnf(socialDataReceiverVF, edge, 16).
vnf(sentimentAnalyzerVF, cloud, 32).
vnf(reportDispatcherVF, cloud, 16).

vnfXUser(socialDataReceiverVF, l, (1, 100000), 16).
vnfXUser(sentimentAnalyzerVF, l, (1, 100000), 32).
vnfXUser(reportDispatcherVF, l, (1, 100000), 16).
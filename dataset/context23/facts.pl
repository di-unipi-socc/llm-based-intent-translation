intent(radiologyAIIntent, medDiagnosticOp, 10000, radiologyPipelineService).

propertyExpectation(affReq, radiologyAIIntent, affinity, dedicated, hard, _, _, lesionAnalyzerVF, _).
propertyExpectation(affReq, radiologyAIIntent, affinity, dedicated, hard, _, _, metadataExtractorVF, _).
propertyExpectation(bwReq, radiologyAIIntent, bandwidth, greater, hard, 500, megabps, dicomIngesterVF, lesionAnalyzerVF).

propertyExpectation(compReq, radiologyAIIntent, compression, _, dicomIngesterVF, _).
propertyExpectation(encReq, radiologyAIIntent, encoding, _, _, secureArchiverVF).

target(radiologyPipelineService, [dicomIngesterVF, lesionAnalyzerVF, metadataExtractorVF, secureArchiverVF]).

vnf(dicomIngesterVF, edge, 16).
vnf(lesionAnalyzerVF, cloud, 32).
vnf(metadataExtractorVF, cloud, 12).
vnf(secureArchiverVF, cloud, 24).

vnfXUser(dicomIngesterVF, l, (1, 10000), 16).
vnfXUser(lesionAnalyzerVF, l, (1, 10000), 32).
vnfXUser(metadataExtractorVF, l, (1, 10000), 12).
vnfXUser(secureArchiverVF, l, (1, 10000), 24).
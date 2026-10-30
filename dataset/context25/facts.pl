intent(govDataIntent, govDataOp, 30000, openDataPortalService).

propertyExpectation(latReq, govDataIntent, latency, lower, hard, 200, ms, dataExtractorVF, downloadProviderVF).
propertyExpectation(bwReq, govDataIntent, bandwidth, greater, soft, 1000, megabps, formatNormalizerVF, metadataEnricherVF).
propertyExpectation(affReq, govDataIntent, affinity, same, hard, _, _, formatNormalizerVF, metadataEnricherVF).

propertyExpectation(cachReq, govDataIntent, caching, _, formatNormalizerVF, _).

target(openDataPortalService, [dataExtractorVF, formatNormalizerVF, metadataEnricherVF, downloadProviderVF]).

vnf(dataExtractorVF, edge, 8).
vnf(formatNormalizerVF, cloud, 16).
vnf(metadataEnricherVF, cloud, 12).
vnf(downloadProviderVF, cloud, 16).

vnfXUser(dataExtractorVF, l, (1, 30000), 8).
vnfXUser(formatNormalizerVF, l, (1, 30000), 16).
vnfXUser(metadataEnricherVF, l, (1, 30000), 12).
vnfXUser(downloadProviderVF, l, (1, 30000), 16).
intent(vodDistributionIntent, vodStreamOp, 80000, vodDistributionService).


propertyExpectation(bwReq, vodDistributionIntent, bandwidth, greater, hard, 10000, megabps, transcoderVF, cachingNodeVF).
propertyExpectation(affReq, vodDistributionIntent, affinity, same, soft, _, _, drmEncryptorVF, transcoderVF).

propertyExpectation(encReq, vodDistributionIntent, encoding, _, drmEncryptorVF, _).
propertyExpectation(decReq, vodDistributionIntent, decoding, _, _, cachingNodeVF).

target(vodDistributionService, [drmEncryptorVF, transcoderVF, cachingNodeVF]).

vnf(drmEncryptorVF, cloud, 16).
vnf(transcoderVF, cloud, 32).
vnf(cachingNodeVF, edge, 12).

vnfXUser(drmEncryptorVF, l, (1, 80000), 16).
vnfXUser(transcoderVF, l, (1, 80000), 32).
vnfXUser(cachingNodeVF, l, (1, 80000), 12).
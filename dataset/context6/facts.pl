intent(govMessagingIntent, govMessagingOp, 50000, govMessagingService).

propertyExpectation(affReq, govMessagingIntent, affinity, same, hard, _, _, sigVerifierVF, integrityCheckerVF).
propertyExpectation(hwReq, govMessagingIntent, totChainHW, lower, soft, 100, gb, _, _).

propertyExpectation(cachReq, govMessagingIntent, caching, _, msgReceiverVF, _).
propertyExpectation(compReq, govMessagingIntent, compression, _, _, legalVaultVF).

target(govMessagingService, [msgReceiverVF, sigVerifierVF, integrityCheckerVF, legalVaultVF]).

vnf(msgReceiverVF, edge, 8).
vnf(sigVerifierVF, cloud, 16).
vnf(integrityCheckerVF, cloud, 12).
vnf(legalVaultVF, cloud, 32).

vnfXUser(msgReceiverVF, l, (1, 50000), 8).
vnfXUser(sigVerifierVF, l, (1, 50000), 16).
vnfXUser(integrityCheckerVF, l, (1, 50000), 12).
vnfXUser(legalVaultVF, l, (1, 50000), 32).
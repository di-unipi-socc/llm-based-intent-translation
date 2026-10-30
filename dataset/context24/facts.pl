intent(eVotingIntent, secureVoteOp, 200000, certifiedVotingService).

propertyExpectation(bwReq, eVotingIntent, bandwidth, greater, soft, 100, megabps, ballotIngesterVF, anonymizerVoteVF).

propertyExpectation(privReq, eVotingIntent, privacy, _, anonymizerVoteVF, _).
propertyExpectation(secReq, eVotingIntent, security, _, _, integrityEnforcerVF).
propertyExpectation(logReq, eVotingIntent, logging, _, _, electoralAuditLoggerVF).

target(certifiedVotingService, [ballotIngesterVF, anonymizerVoteVF, integrityEnforcerVF, voteCounterVF, electoralAuditLoggerVF]).

vnf(ballotIngesterVF, edge, 12).
vnf(anonymizerVoteVF, cloud, 16).
vnf(integrityEnforcerVF, cloud, 24).
vnf(voteCounterVF, cloud, 16).
vnf(electoralAuditLoggerVF, cloud, 12).

vnfXUser(ballotIngesterVF, l, (1, 200000), 12).
vnfXUser(anonymizerVoteVF, l, (1, 200000), 16).
vnfXUser(integrityEnforcerVF, l, (1, 200000), 24).
vnfXUser(voteCounterVF, l, (1, 200000), 16).
vnfXUser(electoralAuditLoggerVF, l, (1, 200000), 12).
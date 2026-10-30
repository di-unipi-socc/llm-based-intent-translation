intent(kycVerificationIntent, onlineBankOp, 10000, digitalIdentityService).

propertyExpectation(encReq, kycVerificationIntent, encoding, _, documentReceiverVF, _).
propertyExpectation(secReq, kycVerificationIntent, security, _, _, authenticityCheckerVF).
propertyExpectation(privReq, kycVerificationIntent, privacy, _, amlMatcherVF, _).
propertyExpectation(compReq, kycVerificationIntent, compression, _, _, profileCreatorVF).

target(digitalIdentityService, [documentReceiverVF, authenticityCheckerVF, amlMatcherVF, profileCreatorVF]).

vnf(documentReceiverVF, edge, 12).
vnf(authenticityCheckerVF, cloud, 24).
vnf(amlMatcherVF, cloud, 16).
vnf(profileCreatorVF, cloud, 16).

vnfXUser(documentReceiverVF, l, (1, 10000), 12).
vnfXUser(authenticityCheckerVF, l, (1, 10000), 24).
vnfXUser(amlMatcherVF, l, (1, 10000), 16).
vnfXUser(profileCreatorVF, l, (1, 10000), 16).
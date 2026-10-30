intent(gdprComplianceIntent, gdprComplianceOp, 5000, gdprVerificationService).

propertyExpectation(latReq, gdprComplianceIntent, latency, lower, soft, 50, ms, dbScannerVF, anonymizerVF).
propertyExpectation(bwReq, gdprComplianceIntent, bandwidth, greater, hard, 50, megabps, anonymizerVF, reportGeneratorVF).


propertyExpectation(privReq, gdprComplianceIntent, privacy, _, dbScannerVF, _).
propertyExpectation(secReq, gdprComplianceIntent, security, _, _, reportGeneratorVF).

target(gdprVerificationService, [dbScannerVF, anonymizerVF, reportGeneratorVF]).

vnf(dbScannerVF, edge, 16).
vnf(anonymizerVF, cloud, 24).
vnf(reportGeneratorVF, cloud, 8).

vnfXUser(dbScannerVF, l, (1, 5000), 16).
vnfXUser(anonymizerVF, l, (1, 5000), 24).
vnfXUser(reportGeneratorVF, l, (1, 5000), 8).
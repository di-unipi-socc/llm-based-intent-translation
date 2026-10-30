intent(teleMonitoringIntent, healthCareOp, 5000, postOperativeTeleMonitoringService).

propertyExpectation(latReq, teleMonitoringIntent, latency, lower, hard, 100, ms, patientDataReceiverVF, doctorNotifierVF).
propertyExpectation(hwReq, teleMonitoringIntent, totChainHW, lower, soft, 80, gb, _, _).

propertyExpectation(privReq, teleMonitoringIntent, privacy, _, patientDataReceiverVF, _).
propertyExpectation(logReq, teleMonitoringIntent, logging, _, _, medicalAlertLoggerVF).

target(postOperativeTeleMonitoringService, [patientDataReceiverVF, cardiacAnomalyAnalyzerVF, medicalAlertLoggerVF, doctorNotifierVF]).

vnf(patientDataReceiverVF, edge, 8).
vnf(cardiacAnomalyAnalyzerVF, cloud, 24).
vnf(medicalAlertLoggerVF, cloud, 12).
vnf(doctorNotifierVF, cloud, 8).

vnfXUser(patientDataReceiverVF, l, (1, 5000), 8).
vnfXUser(cardiacAnomalyAnalyzerVF, l, (1, 5000), 24).
vnfXUser(medicalAlertLoggerVF, l, (1, 5000), 12).
vnfXUser(doctorNotifierVF, l, (1, 5000), 8).
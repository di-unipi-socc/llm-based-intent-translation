intent(liveSubsIntent, liveSubsOp, 10000, liveSubtitlingService).

propertyExpectation(hwReq, liveSubsIntent, totChainHW, lower, soft, 100, gb, _, _).
propertyExpectation(latReq, liveSubsIntent, latency, lower, hard, 70, ms, speechToTextVF, subtitleInjectorVF).

propertyExpectation(cachReq, liveSubsIntent, caching, _, audioExtractorVF, _).

target(liveSubtitlingService, [audioExtractorVF, speechToTextVF, multiTranslatorVF, subtitleInjectorVF]).

vnf(audioExtractorVF, edge, 8).
vnf(speechToTextVF, cloud, 32).
vnf(multiTranslatorVF, cloud, 24).
vnf(subtitleInjectorVF, edge, 12).

vnfXUser(audioExtractorVF, l, (1, 10000), 8).
vnfXUser(speechToTextVF, l, (1, 10000), 32).
vnfXUser(multiTranslatorVF, l, (1, 10000), 24).
vnfXUser(subtitleInjectorVF, l, (1, 10000), 12).
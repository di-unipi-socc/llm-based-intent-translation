intent(corpWebSecurityIntent, corpITOp, 5000, corpWebSecurityService).

propertyExpectation(lat_req, corpWebSecurityIntent, latency, lower, hard, 25, ms, webFilterVF, malwareScannerVF).
propertyExpectation(bw_req, corpWebSecurityIntent, bandwidth, greater, hard, 500, megabps, malwareScannerVF, dlpEngineVF).

target(corpWebSecurityService, [webFilterVF, malwareScannerVF, dlpEngineVF]).

vnf(webFilterVF, edge, 4).
vnf(malwareScannerVF, cloud, 16).
vnf(dlpEngineVF, cloud, 8).

vnfXUser(webFilterVF, l, (1, 5000), 4).
vnfXUser(malwareScannerVF, l, (1, 5000), 16).
vnfXUser(dlpEngineVF, l, (1, 5000), 8).
intent(eInvoiceIntent, eInvoiceOp, 50000, electronicInvoicingService).

propertyExpectation(hwReq, eInvoiceIntent, totChainHW, lower, hard, 150, gb, _, _).
propertyExpectation(latReq, eInvoiceIntent, latency, lower, hard, 30, ms, xmlConverterVF, digitalSignerVF).
propertyExpectation(bwReq, eInvoiceIntent, bandwidth, greater, soft, 100, megabps, digitalSignerVF, taxAuthorityTransmitterVF).


target(electronicInvoicingService, [saleDataCollectorVF, xmlConverterVF, digitalSignerVF, taxAuthorityTransmitterVF]).

vnf(saleDataCollectorVF, edge, 8).
vnf(xmlConverterVF, cloud, 16).
vnf(digitalSignerVF, cloud, 12).
vnf(taxAuthorityTransmitterVF, cloud, 8).

vnfXUser(saleDataCollectorVF, l, (1, 50000), 8).
vnfXUser(xmlConverterVF, l, (1, 50000), 16).
vnfXUser(digitalSignerVF, l, (1, 50000), 12).
vnfXUser(taxAuthorityTransmitterVF, l, (1, 50000), 8).
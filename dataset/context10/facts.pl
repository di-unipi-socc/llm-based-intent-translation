intent(render3DIntent, cinemaRenderOp, 5000, render3DService).

propertyExpectation(hwReq, render3DIntent, totChainHW, lower, soft, 800, gb, _, _).

propertyExpectation(compReq, render3DIntent, compression, _, sceneReceiverVF, _).
propertyExpectation(cachReq, render3DIntent, caching, _, _, colorGraderVF).

target(render3DService, [sceneReceiverVF, assetValidatorVF, renderDistributorVF, frameAssemblerVF, colorGraderVF]).

vnf(sceneReceiverVF, edge, 16).
vnf(assetValidatorVF, cloud, 12).
vnf(renderDistributorVF, cloud, 32).
vnf(frameAssemblerVF, cloud, 24).
vnf(colorGraderVF, cloud, 20).

vnfXUser(sceneReceiverVF, l, (1, 5000), 16).
vnfXUser(assetValidatorVF, l, (1, 5000), 12).
vnfXUser(renderDistributorVF, l, (1, 5000), 32).
vnfXUser(frameAssemblerVF, l, (1, 5000), 24).
vnfXUser(colorGraderVF, l, (1, 5000), 20).
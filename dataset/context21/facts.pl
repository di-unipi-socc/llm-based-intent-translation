intent(autonomousWarehouseIntent, autoWarehouseOp, 500, autonomousControlService).

propertyExpectation(latReq, autonomousWarehouseIntent, latency, lower, hard, 500, ms, sensorDataDecoderVF, commandEncoderVF).

propertyExpectation(decReq, autonomousWarehouseIntent, decoding, _, sensorDataDecoderVF, _).
propertyExpectation(encReq, autonomousWarehouseIntent, encoding, _, _, commandEncoderVF).

target(autonomousControlService, [sensorDataDecoderVF, collisionPathSolverVF, commandEncoderVF]).

vnf(sensorDataDecoderVF, edge, 16).
vnf(collisionPathSolverVF, cloud, 32).
vnf(commandEncoderVF, edge, 16).

vnfXUser(sensorDataDecoderVF, l, (1, 500), 16).
vnfXUser(collisionPathSolverVF, l, (1, 500), 32).
vnfXUser(commandEncoderVF, l, (1, 500), 16).
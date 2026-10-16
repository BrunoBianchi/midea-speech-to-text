// Gateway/Orchestrator entrypoint (skeleton).
//
// Wires together the reverse proxy, the single producer, the lane sequencer,
// the retry system and the SSE channel. Those are implemented in later tasks;
// this file only establishes the module layout.

'use strict';

const contracts = require('./contracts');

module.exports = { contracts };

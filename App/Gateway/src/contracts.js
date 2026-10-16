// Re-export of the shared cross-language contracts for the Gateway.
//
// Canonical module: App/shared/contracts.js (loaded from App/shared/contracts.json).
// Gateway code should import from here:
//   const { ROUTING_KEYS, STATUS, LANE, STATE, SSE_EVENTS } = require('./contracts');

'use strict';

module.exports = require('../../shared/contracts');

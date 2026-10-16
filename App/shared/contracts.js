// Shared cross-language contracts for the Node.js Gateway and workers.
//
// Values are loaded from `contracts.json`, the single source of truth shared
// with the Python side (`contracts.py`). Do NOT hardcode values here; edit
// `contracts.json` so both languages stay in sync.

'use strict';

const fs = require('fs');
const path = require('path');

const CONTRACTS = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'contracts.json'), 'utf8')
);

/** Closed set of routing keys for the direct-exchange. */
const ROUTING_KEYS = Object.freeze({ ...CONTRACTS.routingKeys });

/** `call_jobs.status` enum. */
const STATUS = Object.freeze({ ...CONTRACTS.status });

/** Lane enum. */
const LANE = Object.freeze({ ...CONTRACTS.lane });

/** `workflow_states.state` enum. */
const STATE = Object.freeze({ ...CONTRACTS.state });

/** SSE progress/result events relayed to the dashboard. */
const SSE_EVENTS = Object.freeze({ ...CONTRACTS.sseEvents });

/** Set of valid routing-key values, for membership checks. */
const VALID_ROUTING_KEYS = Object.freeze(new Set(Object.values(ROUTING_KEYS)));

/**
 * @param {string} routingKey
 * @returns {boolean} true when the routing key belongs to the closed set.
 */
function isValidRoutingKey(routingKey) {
  return VALID_ROUTING_KEYS.has(routingKey);
}

module.exports = {
  ROUTING_KEYS,
  STATUS,
  LANE,
  STATE,
  SSE_EVENTS,
  VALID_ROUTING_KEYS,
  isValidRoutingKey,
};

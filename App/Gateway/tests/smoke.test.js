// Smoke test for the Node.js test framework and shared contracts (Task 1).
import { describe, it, expect } from 'vitest';
import {
  ROUTING_KEYS,
  STATUS,
  LANE,
  STATE,
  SSE_EVENTS,
  isValidRoutingKey,
} from '../src/contracts.js';

describe('vitest smoke', () => {
  it('runs', () => {
    expect(true).toBe(true);
  });
});

describe('shared contracts', () => {
  it('exposes the closed set of routing keys', () => {
    expect(ROUTING_KEYS.AUDIO).toBe('routingKey.audio');
    expect(ROUTING_KEYS.TRANSCRIPT).toBe('routingKey.transcript');
    expect(ROUTING_KEYS.AI).toBe('routingKey.AI');
    expect(isValidRoutingKey('routingKey.audio')).toBe(true);
    expect(isValidRoutingKey('routingKey.bogus')).toBe(false);
  });

  it('exposes status/lane/state/sse enums', () => {
    expect(new Set(Object.values(STATUS))).toEqual(
      new Set(['RECEIVED', 'NOISE', 'TRANSCRIPT', 'AI', 'DONE', 'FAILED'])
    );
    expect(new Set(Object.values(LANE))).toEqual(
      new Set(['NOISE', 'TRANSCRIPT', 'AI'])
    );
    expect(new Set(Object.values(STATE))).toEqual(
      new Set(['QUEUED', 'PROCESSING', 'SUCCESS', 'FAILED'])
    );
    expect(new Set(Object.values(SSE_EVENTS))).toEqual(
      new Set(['NOISE_DONE', 'TRANSCRIPT_DONE', 'AI_DONE', 'FAILED'])
    );
  });
});

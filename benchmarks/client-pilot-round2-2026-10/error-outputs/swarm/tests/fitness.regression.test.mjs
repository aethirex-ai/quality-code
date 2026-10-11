import test from 'node:test';
import assert from 'node:assert/strict';
import { canEnroll, cancellationRefund, chronologicalClasses } from '../src/fitness.mjs';

test('enrollment closes at capacity and at zero capacity', () => {
  assert.equal(canEnroll({ confirmed: 0, capacity: 1 }), true);
  assert.equal(canEnroll({ confirmed: 1, capacity: 1 }), false);
  assert.equal(canEnroll({ confirmed: 0, capacity: 0 }), false);
});

test('cancellation exactly 24 hours before class earns the full refund', () => {
  assert.equal(cancellationRefund({ startMs: 86400000, cancelledMs: 0, paidCents: 500 }), 500);
  assert.equal(cancellationRefund({ startMs: 86399999, cancelledMs: 0, paidCents: 500 }), 0);
});

test('class ordering returns a new stable-sorted array without mutating inputs', () => {
  const first = { id: 'first', startMs: 1 };
  const later = { id: 'later', startMs: 2 };
  const tied = { id: 'tied', startMs: 1 };
  const input = [later, first, tied];
  const result = chronologicalClasses(input);

  assert.notStrictEqual(result, input);
  assert.deepEqual(result, [first, tied, later]);
  assert.deepEqual(input, [later, first, tied]);
});

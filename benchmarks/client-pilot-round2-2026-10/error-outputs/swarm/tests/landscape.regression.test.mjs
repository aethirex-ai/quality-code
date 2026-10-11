import test from 'node:test';
import assert from 'node:assert/strict';
import { estimateCents, withinBudget } from '../src/landscape.mjs';

test('estimateCents sums each full line amount, including zero quantities', () => {
  const items = [
    { quantity: 3, unitCents: 10 },
    { quantity: 0, unitCents: 900 },
    { quantity: 2, unitCents: 7 },
  ];
  const snapshot = structuredClone(items);

  assert.equal(estimateCents(items), 44);
  assert.deepEqual(items, snapshot);
  assert.equal(estimateCents([]), 0);
});

test('estimateCents rejects unsafe products and sums', () => {
  assert.throws(
    () => estimateCents([{ quantity: Number.MAX_SAFE_INTEGER, unitCents: 2 }]),
    RangeError,
  );
  assert.throws(
    () => estimateCents([
      { quantity: Number.MAX_SAFE_INTEGER, unitCents: 1 },
      { quantity: 1, unitCents: 1 },
    ]),
    RangeError,
  );
});

test('withinBudget accepts zero estimates and exact budget equality', () => {
  assert.equal(withinBudget({ estimateCents: 0, budgetCents: 0 }), true);
  assert.equal(withinBudget({ estimateCents: 10, budgetCents: 10 }), true);
  assert.equal(withinBudget({ estimateCents: 11, budgetCents: 10 }), false);
});

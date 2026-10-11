import test from 'node:test';
import assert from 'node:assert/strict';
import { quoteStay, staysOverlap, guestBadge } from '../src/hotel.mjs';
import { canEnroll, cancellationRefund, chronologicalClasses } from '../src/fitness.mjs';
import { estimateCents, withinBudget } from '../src/landscape.mjs';

const stay = { checkIn: '2028-06-01', checkOut: '2028-06-02' };

test('quoteStay rounds the final discounted total half upward once', () => {
  assert.equal(quoteStay({ ...stay, nightlyCents: 1, discountPercent: 50 }), 1);
  assert.equal(quoteStay({ ...stay, nightlyCents: 1, discountPercent: 51 }), 0);
  assert.equal(quoteStay({ ...stay, nightlyCents: 1, discountPercent: 49 }), 1);
  assert.equal(quoteStay({ ...stay, checkOut: '2028-06-04', nightlyCents: 1, discountPercent: 50 }), 2);
  assert.equal(quoteStay({ ...stay, nightlyCents: 100 }), 100);
  assert.equal(quoteStay({ ...stay, nightlyCents: 100, discountPercent: 100 }), 0);
});

test('staysOverlap treats adjoining stays as disjoint in both orders', () => {
  const next = { checkIn: '2028-06-02', checkOut: '2028-06-03' };
  assert.equal(staysOverlap(stay, next), false);
  assert.equal(staysOverlap(next, stay), false);
  assert.equal(staysOverlap(stay, stay), true);
  assert.equal(staysOverlap(stay, { checkIn: '2028-05-31', checkOut: '2028-06-03' }), true);
});

test('guestBadge encodes all five special characters without re-encoding replacements', () => {
  assert.equal(guestBadge("O'Brien"), "<span data-guest='O&#39;Brien'>O&#39;Brien</span>");
  const encoded = '&amp;&lt;&gt;&quot;&#39; &amp;lt;';
  assert.equal(guestBadge('&<>"\' &lt;'), `<span data-guest='${encoded}'>${encoded}</span>`);
  assert.equal(guestBadge(''), "<span data-guest=''></span>");
  assert.throws(() => guestBadge(1), TypeError);
});

test('canEnroll closes full and zero-capacity classes', () => {
  assert.equal(canEnroll({ confirmed: 6, capacity: 6 }), false);
  assert.equal(canEnroll({ confirmed: 0, capacity: 0 }), false);
  assert.equal(canEnroll({ confirmed: 7, capacity: 6 }), false);
  assert.equal(canEnroll({ confirmed: 5, capacity: 6 }), true);
});

test('cancellationRefund includes exactly 24 hours and rejects cancellation after start', () => {
  const input = { startMs: 172800000, cancelledMs: 86400000, paidCents: 2500 };
  assert.equal(cancellationRefund(input), 2500);
  assert.equal(cancellationRefund({ ...input, cancelledMs: input.cancelledMs + 1 }), 0);
  assert.equal(cancellationRefund({ ...input, cancelledMs: input.cancelledMs - 1 }), 2500);
  assert.equal(cancellationRefund({ ...input, cancelledMs: input.startMs }), 0);
  assert.throws(() => cancellationRefund({ ...input, cancelledMs: input.startMs + 1 }), RangeError);
});

test('chronologicalClasses returns a new stable array without changing input records or order', () => {
  const classes = [{ id: 'later', startMs: 2 }, { id: 'first', startMs: 1 }, { id: 'tie', startMs: 1 }];
  const original = structuredClone(classes);
  const sorted = chronologicalClasses(classes);
  assert.notStrictEqual(sorted, classes);
  assert.deepEqual(sorted.map(item => item.id), ['first', 'tie', 'later']);
  assert.deepEqual(classes, original);
  assert.strictEqual(sorted[0], classes[1]);
  const frozen = Object.freeze(classes.map(item => Object.freeze({ ...item })));
  assert.deepEqual(chronologicalClasses(frozen).map(item => item.id), ['first', 'tie', 'later']);
  for (const input of [[], [{ id: 'only', startMs: 0 }]]) {
    assert.notStrictEqual(chronologicalClasses(input), input);
  }
});

test('estimateCents adds quantity times unit price, including zero quantities', () => {
  const items = Object.freeze([
    Object.freeze({ quantity: 3, unitCents: 125 }),
    Object.freeze({ quantity: 0, unitCents: 999 }),
    Object.freeze({ quantity: 2, unitCents: 50 }),
  ]);
  assert.equal(estimateCents(items), 475);
  assert.equal(estimateCents([]), 0);
  assert.equal(estimateCents([{ quantity: 0, unitCents: Number.MAX_SAFE_INTEGER }, { quantity: 1, unitCents: 1 }]), 1);
});

test('estimateCents checks overflow against the accumulated extended prices', () => {
  const unitCents = 4503599627370495;
  assert.equal(estimateCents([{ quantity: 2, unitCents }]), 9007199254740990);
  assert.throws(() => estimateCents([{ quantity: 2, unitCents }, { quantity: 1, unitCents: 2 }]), RangeError);
  assert.throws(() => estimateCents([{ quantity: 2, unitCents: Number.MAX_SAFE_INTEGER }]), RangeError);
});

test('withinBudget includes equal and zero budgets', () => {
  assert.equal(withinBudget({ estimateCents: 500, budgetCents: 500 }), true);
  assert.equal(withinBudget({ estimateCents: 0, budgetCents: 0 }), true);
  assert.equal(withinBudget({ estimateCents: 499, budgetCents: 500 }), true);
  assert.equal(withinBudget({ estimateCents: 501, budgetCents: 500 }), false);
});

test('quoteStay validates calendar intervals, money and the pre-discount precision bound', () => {
  assert.equal(quoteStay({ checkIn: '2028-02-28', checkOut: '2028-03-01', nightlyCents: 100 }), 200);
  assert.equal(quoteStay({ checkIn: '2028-03-25', checkOut: '2028-03-27', nightlyCents: 100 }), 200);
  assert.equal(quoteStay({ ...stay, nightlyCents: 90071992547409 }), 90071992547409);
  for (const discountPercent of [0, 100]) {
    assert.throws(() => quoteStay({ ...stay, nightlyCents: 90071992547410, discountPercent }), RangeError);
  }
  for (const checkIn of ['2027-02-29', '2028-04-31', '2028-6-01', null]) {
    assert.throws(() => quoteStay({ ...stay, checkIn, nightlyCents: 1 }), RangeError);
  }
  for (const checkOut of [stay.checkIn, '2028-05-31']) {
    assert.throws(() => quoteStay({ ...stay, checkOut, nightlyCents: 1 }), RangeError);
    assert.throws(() => staysOverlap({ ...stay, checkOut }, stay), RangeError);
    assert.throws(() => staysOverlap(stay, { ...stay, checkOut }), RangeError);
  }
  for (const discountPercent of [-1, 101, 0.5, '50', null, NaN, Infinity]) {
    assert.throws(() => quoteStay({ ...stay, nightlyCents: 1, discountPercent }), RangeError);
  }
});

test('numeric fields reject missing, wrong-type, negative, fractional and unsafe values', () => {
  const invalid = [undefined, null, '1', true, 1n, NaN, Infinity, -1, 0.5, Number.MAX_SAFE_INTEGER + 1];
  const cases = [
    [quoteStay, { ...stay, nightlyCents: 1 }, ['nightlyCents']],
    [canEnroll, { confirmed: 0, capacity: 1 }, ['confirmed', 'capacity']],
    [cancellationRefund, { startMs: 1, cancelledMs: 0, paidCents: 1 }, ['startMs', 'cancelledMs', 'paidCents']],
    [withinBudget, { estimateCents: 0, budgetCents: 1 }, ['estimateCents', 'budgetCents']],
  ];
  for (const [fn, input, fields] of cases) {
    for (const field of fields) {
      for (const value of invalid) assert.throws(() => fn({ ...input, [field]: value }), RangeError);
    }
  }
  for (const value of invalid) {
    assert.throws(() => chronologicalClasses([{ id: 'x', startMs: value }]), RangeError);
    assert.throws(() => estimateCents([{ quantity: value, unitCents: 1 }]), RangeError);
    assert.throws(() => estimateCents([{ quantity: 0, unitCents: value }]), RangeError);
  }
  assert.throws(() => chronologicalClasses([{ startMs: 0 }]), TypeError);
  assert.throws(() => chronologicalClasses([{ id: 1, startMs: 0 }]), TypeError);
  assert.throws(() => chronologicalClasses(null), TypeError);
  assert.throws(() => estimateCents(null), TypeError);
});

import test from 'node:test';
import assert from 'node:assert/strict';
import { quoteStay, staysOverlap, guestBadge } from '../src/hotel.mjs';

test('stay discounts round the final total half upward once', () => {
  const stay = Object.freeze({ checkIn: '2028-06-01', checkOut: '2028-06-02', nightlyCents: 1 });
  assert.equal(quoteStay({ ...stay, discountPercent: 50 }), 1);
  assert.equal(quoteStay({ ...stay, discountPercent: 51 }), 0);
  assert.equal(quoteStay({ ...stay, discountPercent: 49 }), 1);
  assert.equal(quoteStay({ ...stay, checkOut: '2028-06-04', discountPercent: 50 }), 2);
  assert.equal(quoteStay(stay), 1);
});

test('stay arithmetic retains exact integer cents at the allowed limit', () => {
  const stay = { checkIn: '2028-06-01', checkOut: '2028-06-02', nightlyCents: Math.floor(Number.MAX_SAFE_INTEGER / 100) };
  // BigInt supplies an independent exact-arithmetic reference near the limit.
  for (const discountPercent of [0, 1, 50, 99, 100]) {
    const expected = Number((BigInt(stay.nightlyCents) * BigInt(100 - discountPercent) + 50n) / 100n);
    assert.equal(quoteStay({ ...stay, discountPercent }), expected);
  }
  assert.throws(() => quoteStay({ ...stay, nightlyCents: stay.nightlyCents + 1, discountPercent: 100 }), RangeError);
});

test('half-open stays exclude adjoining dates in either argument order', () => {
  const first = Object.freeze({ checkIn: '2028-06-01', checkOut: '2028-06-02' });
  const next = Object.freeze({ checkIn: '2028-06-02', checkOut: '2028-06-03' });
  assert.equal(staysOverlap(first, next), false);
  assert.equal(staysOverlap(next, first), false);
  assert.equal(staysOverlap(first, first), true);
  assert.throws(() => staysOverlap(first, { ...next, checkOut: next.checkIn }), RangeError);
});

test('guest badge encodes all special characters once in attribute and text', () => {
  const encoded = 'O&#39;Reilly &amp; &lt;&gt;&quot; &amp;lt;';
  assert.equal(guestBadge('O\'Reilly & <>" &lt;'), `<span data-guest='${encoded}'>${encoded}</span>`);
});

test('date fields reject non-string types separately from invalid date strings', () => {
  const stay = { checkIn: '2028-06-01', checkOut: '2028-06-02', nightlyCents: 1 };
  for (const value of [undefined, null, 1, true, [], {}, () => {}]) {
    for (const field of ['checkIn', 'checkOut']) {
      const invalid = { ...stay, [field]: value };
      assert.throws(() => quoteStay(invalid), TypeError);
      assert.throws(() => staysOverlap(invalid, stay), TypeError);
      assert.throws(() => staysOverlap(stay, invalid), TypeError);
    }
  }
  for (const checkIn of ['', '2028-6-01', '2027-02-29', '2028-04-31']) {
    assert.throws(() => quoteStay({ ...stay, checkIn }), RangeError);
  }
});

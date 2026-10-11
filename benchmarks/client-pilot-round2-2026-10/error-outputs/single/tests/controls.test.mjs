import test from 'node:test';
import assert from 'node:assert/strict';
import { quoteStay, staysOverlap, guestBadge } from '../src/hotel.mjs';
import { canEnroll, cancellationRefund, chronologicalClasses } from '../src/fitness.mjs';
import { estimateCents, withinBudget } from '../src/landscape.mjs';
test('hotel ordinary quote and overlapping stays', () => {
  assert.equal(quoteStay({checkIn:'2028-02-28',checkOut:'2028-03-01',nightlyCents:10000,discountPercent:10}),18000);
  assert.equal(staysOverlap({checkIn:'2027-04-01',checkOut:'2027-04-05'},{checkIn:'2027-04-03',checkOut:'2027-04-07'}),true);
  assert.equal(guestBadge('A & B'),"<span data-guest='A &amp; B'>A &amp; B</span>");
  assert.throws(() => quoteStay({checkIn:'2027-02-29',checkOut:'2027-03-02',nightlyCents:100}),RangeError);
});
test('studio ordinary enrollment and advance cancellation', () => {
  assert.equal(canEnroll({confirmed:3,capacity:6}),true);
  assert.equal(cancellationRefund({startMs:200000000,cancelledMs:100000000,paidCents:2500}),2500);
  assert.deepEqual(chronologicalClasses([{id:'a',startMs:2},{id:'b',startMs:1}]).map(x=>x.id),['b','a']);
  assert.throws(()=>canEnroll({confirmed:-1,capacity:5}),RangeError);
});
test('landscape ordinary estimate and budget', () => {
  assert.equal(estimateCents([{quantity:1,unitCents:12500},{quantity:1,unitCents:5000}]),17500);
  assert.equal(withinBudget({estimateCents:17500,budgetCents:20000}),true);
  assert.throws(()=>estimateCents([{quantity:1,unitCents:1.5}]),RangeError);
});

test('public record arguments reject non-record values', () => {

   const badRecords = [undefined, null, 'x', 7, true, 1n, Symbol('x'), [], () => {}];
   const goodStay = {checkIn:'2028-06-01',checkOut:'2028-06-03'};
   for (const value of badRecords) {
     assert.throws(()=>quoteStay(value),TypeError);
     assert.throws(()=>staysOverlap(value,goodStay),TypeError);
     assert.throws(()=>staysOverlap(goodStay,value),TypeError);
     assert.throws(()=>canEnroll(value),TypeError);
     assert.throws(()=>cancellationRefund(value),TypeError);
     assert.throws(()=>chronologicalClasses([value]),TypeError);
     assert.throws(()=>estimateCents([value]),TypeError);
     assert.throws(()=>withinBudget(value),TypeError);
   }
   const arrayRecord = Object.assign([], {id:'x', startMs:0, quantity:1, unitCents:1});
   const functionRecord = Object.assign(()=>{}, {id:'x', startMs:0, quantity:1, unitCents:1});
   for (const value of [arrayRecord,functionRecord]) {
     assert.throws(()=>chronologicalClasses([value]),TypeError);
     assert.throws(()=>estimateCents([value]),TypeError);
   }
});

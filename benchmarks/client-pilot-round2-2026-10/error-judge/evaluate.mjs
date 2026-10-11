import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const root = resolve(process.argv[2] ?? '../error-fixture');
const load = name => import(pathToFileURL(resolve(root, 'src', name + '.mjs')).href);
const [hotel, fitness, landscape] = await Promise.all(['hotel','fitness','landscape'].map(load));
const groups = [
 ['H_PRICE', () => {
   assert.equal(hotel.quoteStay({checkIn:'2028-06-01',checkOut:'2028-06-02',nightlyCents:105,discountPercent:10}),95);
   assert.equal(hotel.quoteStay({checkIn:'2028-06-01',checkOut:'2028-06-04',nightlyCents:101,discountPercent:15}),258);
 }],
 ['H_INTERVAL', () => {
   const a={checkIn:'2028-06-01',checkOut:'2028-06-03'}, b={checkIn:'2028-06-03',checkOut:'2028-06-05'};
   assert.equal(hotel.staysOverlap(a,b),false);
   assert.equal(hotel.staysOverlap(b,a),false);
 }],
 ['H_HTML', () => {
   assert.equal(hotel.guestBadge("O'Neil"),"<span data-guest='O&#39;Neil'>O&#39;Neil</span>");
   assert.equal(hotel.guestBadge("' autofocus onfocus='alert(1)"),"<span data-guest='&#39; autofocus onfocus=&#39;alert(1)'>&#39; autofocus onfocus=&#39;alert(1)</span>");
 }],
 ['F_CAPACITY', () => {
   assert.equal(fitness.canEnroll({confirmed:12,capacity:12}),false);
   assert.equal(fitness.canEnroll({confirmed:0,capacity:0}),false);
 }],
 ['F_REFUND', () => {
   assert.equal(fitness.cancellationRefund({startMs:172800000,cancelledMs:86400000,paidCents:3900}),3900);
   assert.equal(fitness.cancellationRefund({startMs:86400000,cancelledMs:0,paidCents:1}),1);
 }],
 ['F_PURITY', () => {
   const a={id:'late',startMs:30},b={id:'early',startMs:10}; const input=[a,b];
   const output=fitness.chronologicalClasses(input);
   assert.deepEqual(input,[a,b]); assert.notEqual(output,input); assert.deepEqual(output,[b,a]);
   const frozen=Object.freeze([{id:'x',startMs:2},{id:'y',startMs:1}]);
   assert.deepEqual(fitness.chronologicalClasses(frozen).map(x=>x.id),['y','x']);
 }],
 ['L_QUANTITY', () => {
   assert.equal(landscape.estimateCents([{quantity:3,unitCents:12500},{quantity:2,unitCents:499}]),38498);
   assert.equal(landscape.estimateCents([{quantity:0,unitCents:9500}]),0);
 }],
 ['L_BUDGET', () => {
   assert.equal(landscape.withinBudget({estimateCents:450000,budgetCents:450000}),true);
   assert.equal(landscape.withinBudget({estimateCents:0,budgetCents:0}),true);
 }],
];
const controls = [
 ['record_validation', () => {
   const badRecords = [undefined, null, 'x', 7, true, 1n, Symbol('x'), [], () => {}];
   const goodStay = {checkIn:'2028-06-01',checkOut:'2028-06-03'};
   for (const value of badRecords) {
     assert.throws(()=>hotel.quoteStay(value),TypeError);
     assert.throws(()=>hotel.staysOverlap(value,goodStay),TypeError);
     assert.throws(()=>hotel.staysOverlap(goodStay,value),TypeError);
     assert.throws(()=>fitness.canEnroll(value),TypeError);
     assert.throws(()=>fitness.cancellationRefund(value),TypeError);
     assert.throws(()=>fitness.chronologicalClasses([value]),TypeError);
     assert.throws(()=>landscape.estimateCents([value]),TypeError);
     assert.throws(()=>landscape.withinBudget(value),TypeError);
   }
   const arrayRecord = Object.assign([], {id:'x', startMs:0, quantity:1, unitCents:1});
   const functionRecord = Object.assign(()=>{}, {id:'x', startMs:0, quantity:1, unitCents:1});
   for (const value of [arrayRecord,functionRecord]) {
     assert.throws(()=>fitness.chronologicalClasses([value]),TypeError);
     assert.throws(()=>landscape.estimateCents([value]),TypeError);
   }
 }],
 ['hotel_dates_prices', () => {
   assert.equal(hotel.quoteStay({checkIn:'2028-02-28',checkOut:'2028-03-01',nightlyCents:10000,discountPercent:10}),18000);
   assert.equal(hotel.quoteStay({checkIn:'2028-03-25',checkOut:'2028-03-28',nightlyCents:1000}),3000);
   assert.equal(hotel.quoteStay({checkIn:'2028-12-31',checkOut:'2029-01-02',nightlyCents:50,discountPercent:100}),0);
   for (const args of [
     {checkIn:'2027-02-29',checkOut:'2027-03-02',nightlyCents:10},
     {checkIn:'2028-01-01',checkOut:'2028-01-01',nightlyCents:10},
     {checkIn:'2028-01-01',checkOut:'2028-01-02',nightlyCents:-1},
     {checkIn:'2028-01-01',checkOut:'2028-01-02',nightlyCents:1,discountPercent:101},
     {checkIn:'2028-01-01',checkOut:'2028-01-02',nightlyCents:1,discountPercent:0.5},
     {checkIn:'2028-01-01',checkOut:'2028-01-02',nightlyCents:Number.MAX_SAFE_INTEGER},
   ]) assert.throws(()=>hotel.quoteStay(args),RangeError);
 }],
 ['hotel_overlap', () => {
   const a={checkIn:'2028-06-01',checkOut:'2028-06-04'};
   assert.equal(hotel.staysOverlap(a,{checkIn:'2028-06-02',checkOut:'2028-06-03'}),true);
   assert.equal(hotel.staysOverlap(a,{checkIn:'2028-06-05',checkOut:'2028-06-07'}),false);
   assert.throws(()=>hotel.staysOverlap(a,{checkIn:'2028-06-05',checkOut:'2028-06-04'}),RangeError);
 }],
 ['hotel_encoding', () => {
   assert.equal(hotel.guestBadge('&<>"'),"<span data-guest='&amp;&lt;&gt;&quot;'>&amp;&lt;&gt;&quot;</span>");
   assert.equal(hotel.guestBadge('&amp;'),"<span data-guest='&amp;amp;'>&amp;amp;</span>");
   assert.equal(hotel.guestBadge(''),"<span data-guest=''></span>");
   assert.throws(()=>hotel.guestBadge(null),TypeError);
 }],
 ['fitness_enrollment', () => {
   assert.equal(fitness.canEnroll({confirmed:4,capacity:5}),true);
   assert.equal(fitness.canEnroll({confirmed:6,capacity:5}),false);
   for(const value of [-1,1.5,NaN,Infinity,'3',Number.MAX_SAFE_INTEGER+1]) assert.throws(()=>fitness.canEnroll({confirmed:value,capacity:5}),RangeError);
 }],
 ['fitness_refunds', () => {
   assert.equal(fitness.cancellationRefund({startMs:172800000,cancelledMs:86399999,paidCents:3900}),3900);
   assert.equal(fitness.cancellationRefund({startMs:172800000,cancelledMs:86400001,paidCents:3900}),0);
   assert.equal(fitness.cancellationRefund({startMs:0,cancelledMs:0,paidCents:1}),0);
   assert.throws(()=>fitness.cancellationRefund({startMs:5,cancelledMs:6,paidCents:1}),RangeError);
   assert.throws(()=>fitness.cancellationRefund({startMs:5,cancelledMs:0,paidCents:1.1}),RangeError);
 }],
 ['fitness_ordering', () => {
   assert.deepEqual(fitness.chronologicalClasses([{id:'b',startMs:2},{id:'c',startMs:2},{id:'a',startMs:1}]).map(x=>x.id),['a','b','c']);
   assert.deepEqual(fitness.chronologicalClasses([]),[]);
   assert.throws(()=>fitness.chronologicalClasses(null),TypeError);
   assert.throws(()=>fitness.chronologicalClasses([{id:1,startMs:0}]),TypeError);
   assert.throws(()=>fitness.chronologicalClasses([{id:'a',startMs:-1}]),RangeError);
 }],
 ['landscape_estimates', () => {
   const input=Object.freeze([Object.freeze({quantity:1,unitCents:9500}),Object.freeze({quantity:1,unitCents:200})]);
   assert.equal(landscape.estimateCents(input),9700); assert.equal(landscape.estimateCents([]),0);
   assert.throws(()=>landscape.estimateCents(null),TypeError);
   assert.throws(()=>landscape.estimateCents([null]),TypeError);
   for(const input of [[{quantity:-1,unitCents:1}],[{quantity:1,unitCents:1.1}],[{quantity:Number.MAX_SAFE_INTEGER,unitCents:2}],[{quantity:1,unitCents:Number.MAX_SAFE_INTEGER},{quantity:1,unitCents:1}]]) assert.throws(()=>landscape.estimateCents(input),RangeError);
 }],
 ['landscape_budgets', () => {
   assert.equal(landscape.withinBudget({estimateCents:999,budgetCents:1000}),true);
   assert.equal(landscape.withinBudget({estimateCents:1001,budgetCents:1000}),false);
   assert.throws(()=>landscape.withinBudget({estimateCents:1.5,budgetCents:1000}),RangeError);
   assert.throws(()=>landscape.withinBudget({estimateCents:1,budgetCents:-1}),RangeError);
 }],
];
const run = cases => cases.map(([id,fn])=>{try{fn();return{id,pass:true}}catch(error){return{id,pass:false,error:error.message}}});
const seeds=run(groups), healthy=run(controls);
const summary={workspace:root,resolvedSeedCount:seeds.filter(x=>x.pass).length,totalSeedCount:seeds.length,seeds,healthyControls:healthy,regressionCount:healthy.filter(x=>!x.pass).length};
console.log(JSON.stringify(summary,null,2));
process.exitCode = summary.resolvedSeedCount===groups.length && summary.regressionCount===0 ? 0 : 1;

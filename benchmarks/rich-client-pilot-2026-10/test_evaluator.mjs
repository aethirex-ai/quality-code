import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {evaluate, exactCents} from './evaluator.mjs';
assert.equal(exactCents('93600',93600),true);
for(const x of ['93600.0','093600','93600 cents','NaN','93601',null])assert.equal(exactCents(x,93600),false);
const temp=await fs.mkdtemp(path.join(os.tmpdir(),'rich-evaluator-test-'));
const valid=path.join(temp,'valid');await fs.mkdir(valid);
const img='<img src="asset.svg" alt="Synthetic fixture geometry">';
const svg='<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20"><rect width="20" height="20" fill="gray"/></svg>';
const clientHTML=(client,file)=>{
 const lighting=client==='lighting';const pages=lighting?['index','collection','planner']:['index','journeys','builder'];
 const nav=pages.map(x=>`<a href="${x}.html">${x}</a>`).join(' ');
 const products=['arc','line','orbit'];const trips=['ridge','fjord','desert'];
 let body='<h1>Synthetic '+client+'</h1>'+img;
 if(file==='collection')body+='<select data-testid="type-filter">'+['all','pendant','wall','table'].map(x=>`<option>${x}</option>`).join('')+'</select>'+products.map((x,i)=>`<article data-testid="product-card" data-product-id="${x}"><h2>${x.toUpperCase()}</h2><button data-testid="open-product" data-product-id="${x}">Detail</button><button data-testid="add-product" data-product-id="${x}">Add</button></article>`).join('')+'<dialog data-testid="product-dialog"><p id="dialog-name"></p><button data-testid="close-product">Close</button></dialog>';
 if(file==='planner')body+='<section id="plan"></section><p data-testid="plan-total" data-total-cents="0">EUR 0</p><form data-testid="project-form"><label>Name<input name="name" required></label><label>Email<input type="email" required></label><label>Project<textarea required></textarea></label><button>Prepare</button><p data-testid="project-status"></p></form>';
 if(file==='journeys')body+='<select data-testid="terrain-filter">'+['all','alpine','coastal','desert'].map(x=>`<option>${x}</option>`).join('')+'</select>'+trips.map(x=>`<article data-testid="journey-card" data-journey-id="${x}"><button data-testid="select-journey" data-journey-id="${x}">${x}</button></article>`).join('');
 if(file==='builder')body+='<label>Journey<select data-testid="journey-select">'+trips.map(x=>`<option>${x}</option>`).join('')+'</select></label><label>Travelers<input data-testid="travelers" type="number" min="1" max="6" required></label><label>Guide<input data-testid="add-guide" type="checkbox"></label><p id="summary"></p><p data-testid="trip-total"></p><section id="itinerary"></section><form data-testid="trip-form"><label>Name<input name="name" required></label><label>Email<input type="email" required></label><button>Prepare</button><p data-testid="trip-status"></p></form>';
 return `<!doctype html><html><head><title>Synthetic fixture ${client} ${file}</title><meta name="description" content="Offline synthetic evaluator test"><link rel="icon" href="data:,"><style>*{box-sizing:border-box}body{margin:10px}img{display:block}button,a,input,select,textarea{max-width:100%}:focus-visible{outline:3px solid blue}dialog{max-width:90vw}</style></head><body><nav>${nav}</nav><span data-testid="plan-count">0</span><main>${body}</main><footer>Fictional portfolio concept by AethDesign</footer><script src="test.js"></script></body></html>`;
};
const js=`
const q=s=>document.querySelector(s);const all=s=>[...document.querySelectorAll(s)];
let plan={};try{const a=JSON.parse(localStorage.getItem('aurel.plan.v1'));if(a&&!Array.isArray(a)&&typeof a==='object')for(const id of ['arc','line','orbit'])if(Number.isInteger(a[id])&&a[id]>=1&&a[id]<=10)plan[id]=a[id];}catch{}
let trip={journey:'ridge',travelers:1,guide:false};try{let t=JSON.parse(localStorage.getItem('meridian.trip.v1'));if(t&&['ridge','fjord','desert'].includes(t.journey)&&Number.isInteger(t.travelers)&&t.travelers>=1&&t.travelers<=6&&typeof t.guide==='boolean')trip=t;}catch{}
const savePlan=()=>{localStorage.setItem('aurel.plan.v1',JSON.stringify(plan));renderPlan()};
function renderPlan(){q('[data-testid="plan-count"]').textContent=Object.values(plan).reduce((a,b)=>a+b,0);if(q('#plan')){q('#plan').innerHTML=Object.entries(plan).map(([id,n])=>'<label>'+id+'<input data-testid="quantity-'+id+'" type="number" min="1" max="10" required value="'+n+'"></label><button data-testid="remove-product" data-product-id="'+id+'">Remove</button>').join('');all('[data-testid^="quantity-"]').forEach(e=>e.onchange=()=>{plan[e.dataset.testid.slice(9)]=Math.max(1,Math.min(10,Math.round(+e.value)||1));savePlan()});all('[data-testid="remove-product"]').forEach(e=>e.onclick=()=>{delete plan[e.dataset.productId];savePlan()});let n=Object.entries(plan).reduce((a,[id,n])=>a+({arc:24900,line:18900,orbit:32900}[id]*n),0);q('[data-testid="plan-total"]').dataset.totalCents=n;q('[data-testid="plan-total"]').textContent='EUR '+n/100;}}
renderPlan();
all('[data-testid="add-product"]').forEach(e=>e.onclick=()=>{plan[e.dataset.productId]=(plan[e.dataset.productId]||0)+1;savePlan()});
all('[data-testid="open-product"]').forEach(e=>e.onclick=()=>{q('#dialog-name').textContent=e.dataset.productId.toUpperCase()+' material and dimension details';q('dialog').showModal()});if(q('[data-testid="close-product"]'))q('[data-testid="close-product"]').onclick=()=>q('dialog').close();
if(q('[data-testid="type-filter"]'))q('[data-testid="type-filter"]').onchange=e=>all('[data-testid="product-card"]').forEach((c,i)=>c.hidden=e.target.value!=='all'&&['pendant','wall','table'][i]!==e.target.value);
if(q('[data-testid="terrain-filter"]'))q('[data-testid="terrain-filter"]').onchange=e=>all('[data-testid="journey-card"]').forEach((c,i)=>c.hidden=e.target.value!=='all'&&['alpine','coastal','desert'][i]!==e.target.value);
all('[data-testid="select-journey"]').forEach(e=>e.onclick=()=>{trip.journey=e.dataset.journeyId;localStorage.setItem('meridian.trip.v1',JSON.stringify(trip));location.href='builder.html'});
function renderTrip(){const j=q('[data-testid="journey-select"]');if(!j)return;j.value=trip.journey;q('[data-testid="travelers"]').value=trip.travelers;q('[data-testid="add-guide"]').checked=trip.guide;let n={ridge:240000,fjord:180000,desert:210000}[trip.journey]*trip.travelers+(trip.guide?60000:0);q('[data-testid="trip-total"]').dataset.totalCents=n;q('[data-testid="trip-total"]').textContent='EUR '+n/100;q('#summary').textContent=trip.journey.toUpperCase()+' '+({ridge:7,fjord:5,desert:6}[trip.journey])+' days '+trip.travelers+' travelers guide '+trip.guide;q('#itinerary').innerHTML=[1,2,3].map(i=>'<details><summary>Day '+i+'</summary><p>'+trip.journey+' day '+i+' explore the fictional landscape along a distinctive route through places and villages.</p></details>').join('');localStorage.setItem('meridian.trip.v1',JSON.stringify(trip))}
renderTrip();if(q('[data-testid="journey-select"]')){q('[data-testid="journey-select"]').onchange=e=>{trip.journey=e.target.value;renderTrip()};q('[data-testid="travelers"]').onchange=e=>{trip.travelers=Math.max(1,Math.min(6,Math.round(+e.target.value)||1));renderTrip()};q('[data-testid="add-guide"]').onchange=e=>{trip.guide=e.target.checked;renderTrip()}}
all('form').forEach(f=>f.onsubmit=e=>{e.preventDefault();f.querySelector('[data-testid$="-status"]').textContent='Local demo specification prepared for your review.'});
`;
for(const client of ['lighting','expedition']){await fs.mkdir(path.join(valid,client));await fs.writeFile(path.join(valid,client,'asset.svg'),svg);await fs.writeFile(path.join(valid,client,'test.js'),js);for(const page of client==='lighting'?['index','collection','planner']:['index','journeys','builder'])await fs.writeFile(path.join(valid,client,page+'.html'),clientHTML(client,page));}
const good=await evaluate(valid,path.join(temp,'good'));
assert.equal(good.fatal,null);assert.equal(good.passed,good.total,JSON.stringify(good.errors));
assert.equal((await fs.readdir(path.join(temp,'good'))).filter(x=>x.endsWith('.png')).length,12);
const rejecting=js.replace("plan[e.dataset.testid.slice(9)]=Math.max(1,Math.min(10,Math.round(+e.value)||1));", "if(!e.checkValidity())return;plan[e.dataset.testid.slice(9)]=+e.value;").replace("trip.travelers=Math.max(1,Math.min(6,Math.round(+e.target.value)||1));", "if(!e.target.checkValidity())return;trip.travelers=+e.target.value;");
for(const client of ['lighting','expedition'])await fs.writeFile(path.join(valid,client,'test.js'),rejecting);
const rejected=await evaluate(valid,path.join(temp,'rejecting'));
assert.equal(rejected.total,good.total);assert.equal(rejected.passed,rejected.total,JSON.stringify(rejected.errors));
const naive=js.replace('Math.max(1,Math.min(10,Math.round(+e.value)||1))','+e.value').replace('Math.max(1,Math.min(6,Math.round(+e.target.value)||1))','+e.target.value');
for(const client of ['lighting','expedition'])await fs.writeFile(path.join(valid,client,'test.js'),naive);
const invalid=await evaluate(valid,path.join(temp,'invalid'));
assert.equal(invalid.total,good.total);assert.equal(invalid.fatal,null);
assert.ok(invalid.results.some(x=>x.name.startsWith('lighting: invalid ARC quantity')&&!x.passed));
assert.ok(invalid.results.some(x=>x.name.startsWith('expedition: invalid travelers')&&!x.passed));
for(const client of ['lighting','expedition'])await fs.writeFile(path.join(valid,client,'test.js'),js);
const script=path.join(valid,'lighting','test.js');await fs.writeFile(script,js.replace('arc:24900','arc:25000'));
const bad=await evaluate(valid,path.join(temp,'bad'));
assert.equal(bad.total,good.total);assert.ok(bad.results.some(x=>x.name==='lighting: add ARC twice count and total'&&!x.passed));assert.ok(bad.passed<bad.total);
await fs.writeFile(path.join(valid,'lighting','collection.html'),clientHTML('lighting','collection').replaceAll('data-testid="type-filter"','data-testid="missing-filter"'));
const missing=await evaluate(valid,path.join(temp,'missing'));
assert.equal(missing.total,good.total);assert.equal(missing.fatal,null);assert.ok(missing.results.some(x=>x.name.startsWith('lighting: filter')&&!x.passed));
console.log(JSON.stringify({checks:good.total,validPassed:good.passed,seededMathFailureDetected:true,seededInvalidHandlersDetected:true,rejectAndRetainAccepted:true,closeButtonChecks:3,invalidEditChecks:8,missingSelectorsBounded:true,screenshots:12}));
await fs.rm(temp,{recursive:true,force:true});

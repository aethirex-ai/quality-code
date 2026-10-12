export const KEY = 'aurel.plan.v1';
export const products = Object.freeze([
  {id:'arc',name:'ARC',type:'pendant',price:24900,dimensions:'1200 × 80 × 60 mm',material:'Brushed copper · opal diffuser',finish:'Brushed copper',description:'A quiet suspended gesture. A slender copper arc gathers warm light along its inner edge, bringing definition to a dining table or long work surface.'},
  {id:'line',name:'LINE',type:'wall',price:18900,dimensions:'600 × 45 × 40 mm',material:'Charcoal aluminium · opal diffuser',finish:'Charcoal',description:'A precise vertical line with a soft edge. Set beside a doorway or along a circulation wall to create a measured rhythm of light.'},
  {id:'orbit',name:'ORBIT',type:'table',price:32900,dimensions:'220 × 220 × 310 mm',material:'Opal glass · charcoal aluminium',finish:'Charcoal / opal',description:'An opal glass sphere balanced on a compact charcoal base. A warm pool of light for a reading corner, sideboard or bedside surface.'}
]);
export const money = cents => new Intl.NumberFormat('en-IE',{style:'currency',currency:'EUR'}).format(cents/100);
export function validQuantity(value, previous=1) {
  if (typeof value !== 'number' && typeof value !== 'string') return previous;
  if (typeof value==='string' && !value.trim()) return previous;
  const n=Number(value);
  return Number.isInteger(n) && n>=1 && n<=10 ? n : previous;
}
export function normalizePlan(value) {
  if (!value || typeof value!=='object' || Array.isArray(value)) return {};
  const plan={};
  for (const p of products) {
    if (Object.hasOwn(value,p.id)) {
      const q=validQuantity(value[p.id],0);
      if(q) plan[p.id]=q;
    }
  }
  return plan;
}
export function parsePlan(raw) {try {return normalizePlan(JSON.parse(raw));} catch {return {};}}
export function addProduct(plan,id) {const next=normalizePlan(plan);if(products.some(p=>p.id===id)) next[id]=Math.min(10,(next[id]||0)+1);return next;}
export function setQuantity(plan,id,value) {const next=normalizePlan(plan);if(next[id])next[id]=validQuantity(value,next[id]);return next;}
export function removeProduct(plan,id) {const next=normalizePlan(plan);delete next[id];return next;}
export function countPlan(plan) {return Object.values(normalizePlan(plan)).reduce((a,b)=>a+b,0);}
export function totalPlan(plan) {const safe=normalizePlan(plan);return products.reduce((sum,p)=>sum+p.price*(safe[p.id]||0),0);}

const items=[];
const count=document.querySelector('[data-testid="bag-count"]');
const panel=document.querySelector('#bag-panel');
const toggle=document.querySelector('.bag-toggle');
const status=document.querySelector('#bag-status');
let toastTimer;
function renderBag(){
  count.textContent=String(items.length);
  document.querySelector('#bag-empty').hidden=items.length>0;
  document.querySelector('#bag-items').replaceChildren(...items.map(item=>{
    const li=document.createElement('li');
    const name=document.createElement('span');name.textContent=item.name;
    const price=document.createElement('span');price.textContent=`€${item.price}`;
    li.append(name,price);return li;
  }));
  document.querySelector('#bag-total').textContent=`€${items.reduce((sum,item)=>sum+item.price,0)}`;
}
function closeBag(){panel.hidden=true;toggle.setAttribute('aria-expanded','false');toggle.focus();}
document.querySelectorAll('.add-button').forEach(button=>button.addEventListener('click',()=>{
  items.push({name:button.dataset.product,price:Number(button.dataset.price)});renderBag();
  status.textContent=`${button.dataset.product} added to your demo bag.`;
  clearTimeout(toastTimer);toastTimer=setTimeout(()=>{status.textContent='';},3500);
}));
toggle.addEventListener('click',()=>{
  const opening=panel.hidden;panel.hidden=!opening;toggle.setAttribute('aria-expanded',String(opening));
  if(opening)document.querySelector('.bag-close').focus();
});
document.querySelector('.bag-close').addEventListener('click',closeBag);
document.querySelector('.clear-bag').addEventListener('click',()=>{items.length=0;renderBag();status.textContent='Your demo bag is empty.';});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!panel.hidden)closeBag();});

const products = [{name:'The Pedestal Bowl',price:68},{name:'The Daily Cup',price:28},{name:'The Stem Vase',price:92}];
const quantities = [0,0,0];
const bag = document.querySelector('#bag');
function renderBag(){
  const count = quantities.reduce((sum,n)=>sum+n,0);
  document.querySelector('[data-testid="bag-count"]').textContent=String(count);
  const list=document.querySelector('#bag-items');list.replaceChildren();
  products.forEach((product,i)=>{if(!quantities[i])return;const item=document.createElement('li');const text=document.createElement('span');text.textContent=`${product.name} × ${quantities[i]} · €${product.price*quantities[i]}`;const remove=document.createElement('button');remove.type='button';remove.textContent='Remove one';remove.setAttribute('aria-label',`Remove one ${product.name} from bag`);remove.addEventListener('click',()=>{quantities[i]--;renderBag();document.querySelector('#close-bag').focus();});item.append(text,remove);list.append(item);});
  document.querySelector('#bag-total').textContent=count?`Demo total: €${products.reduce((sum,p,i)=>sum+p.price*quantities[i],0)} · ${count} ${count===1?'object':'objects'}`:'Your bag is waiting for something thoughtful.';
}
document.querySelectorAll('[data-product]').forEach(button=>button.addEventListener('click',()=>{const i=Number(button.dataset.product);quantities[i]++;renderBag();document.querySelector('#bag-status').textContent=`${products[i].name} added to your demo bag. No purchase has been made.`;}));
document.querySelector('#open-bag').addEventListener('click',()=>bag.showModal());
document.querySelector('#close-bag').addEventListener('click',()=>bag.close());
document.querySelector('#continue-browsing').addEventListener('click',()=>bag.close());

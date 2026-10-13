import assert from 'node:assert/strict';import {mkdtemp,mkdir,cp,readFile,writeFile,rm} from 'node:fs/promises';import {tmpdir} from 'node:os';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {evaluate as before} from './evaluate-reload-only.mjs';import {evaluate} from './evaluate.mjs';
const root=path.dirname(fileURLToPath(import.meta.url)),out=path.resolve(process.argv[2]);await mkdir(out,{recursive:true});const work=await mkdtemp(path.join(tmpdir(),'front-tab-proof-'));const results={};
try{
 await cp(path.join(root,'fixture'),work,{recursive:true});let html=await readFile(path.join(work,'index.html'),'utf8');html=html.replace("const mode='__MODE__'","let pendingTab=null;const mode='__MODE__'");
 html=html.replace('async function overview(){',"async function overview(){section='brief';");html=html.replace("map(t=>button('tab-'+t,t))", "map(t=>`<button data-testid=\"tab-${t}\" aria-selected=\"${section===t}\">${t}</button>`)");
 // Staff form is already visible on brief, as in the measured app. Rendering
 // the chosen tab replaces it only once the advertised selection is true.
 html=html.replace("renderSection();if(mode==='overflow')", "renderSection();if(user.role==='staff'&&section==='brief'){const saved=section;section='revisions';renderSection();section=saved;}if(mode==='overflow')");
 html=html.replace("section=t;renderSection();", "pendingTab=t;setTimeout(()=>{if(pendingTab===t){pendingTab=null;section=t;render();}},250);");
 html=html.replace("el('publish-revision').onclick=async()=>{","el('publish-revision').onclick=async()=>{if(!el('revision-title').value.trim()||!el('revision-summary').value.trim())return;");html=html.replace('</script>',`document.addEventListener('input',e=>{if(e.target.dataset.testid==='revision-summary'&&pendingTab){const next=pendingTab;setTimeout(()=>{if(pendingTab===next){pendingTab=null;section=next;render();}},0);}});</script>`);await writeFile(path.join(work,'index.html'),html);
 const old=await before({site:work,out:path.join(out,'before'),screenshots:false});assert.equal(old.groups.find(g=>g.name==='staff_publish_reopens_history_activity').status,'fail');assert.equal(old.groups.find(g=>g.name==='authorized_cards').status,'pass');results.before={passed:old.passed,publish:'fail'};
 const healthy=await evaluate({site:work,out:path.join(out,'healthy'),screenshots:false});assert.equal(healthy.passed,11);results.healthy={passed:healthy.passed};
 const negative=await evaluate({site:work,out:path.join(out,'negative-publish'),env:{FRONTEND_FIXTURE_MODE:'publish'},screenshots:false});assert.equal(negative.groups.find(g=>g.name==='staff_publish_reopens_history_activity').status,'fail');assert.equal(negative.groups.find(g=>g.name==='authorized_cards').status,'pass');results.negative={publish:'fail',healthyControl:'authorized_cards:pass'};
 await writeFile(path.join(out,'tab-regression.json'),JSON.stringify(results,null,2));console.log(JSON.stringify({status:'pass',...results}));
}finally{await rm(work,{recursive:true,force:true});}

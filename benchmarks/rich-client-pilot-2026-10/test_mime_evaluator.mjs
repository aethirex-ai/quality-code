import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {evaluate as original} from './evaluator.mjs';
import {evaluate as corrected} from './evaluator-mime-corrected.mjs';
const root=await fs.mkdtemp(path.join(os.tmpdir(),'rich-module-mime-'));
try {
 for(const client of ['lighting','expedition']) {
  const dir=path.join(root,client);await fs.mkdir(dir);
  await fs.writeFile(path.join(dir,'dependency.mjs'),'export const title="Module loaded";');
  await fs.writeFile(path.join(dir,'app.mjs'),'import {title} from "./dependency.mjs";document.title=title;');
  for(const name of client==='lighting'?['index','collection','planner']:['index','journeys','builder'])await fs.writeFile(path.join(dir,name+'.html'),'<html><head><title></title><meta name="description" content="Module MIME regression"><script type="module" src="app.mjs"></script></head><body><nav></nav><main><h1>Synthetic module probe</h1></main><footer>Fictional portfolio concept by AethDesign</footer></body></html>');
 }
 const before=await original(root,path.join(root,'before'));
 const after=await corrected(root,path.join(root,'after'));
 assert.equal(before.total,142);assert.equal(after.total,142);
 assert.ok(before.runtimeErrors.some(x=>x.includes('MIME type')));
 assert.equal(after.runtimeErrors.length,0);
 assert.equal(before.results.filter(x=>x.name.endsWith(': metadata')&&x.passed).length,0);
 assert.equal(after.results.filter(x=>x.name.endsWith(': metadata')&&x.passed).length,12);
 console.log('PASS: original hosting reproduces module MIME rejection; corrected hosting loads modules and imports on all six routes/two widths. Other missing-contract failures are intentional in this narrow fixture.');
} finally {await fs.rm(root,{recursive:true,force:true});}

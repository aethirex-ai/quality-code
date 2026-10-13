import assert from 'node:assert/strict';import {mkdir,writeFile} from 'node:fs/promises';import path from 'node:path';import {fileURLToPath} from 'node:url';import {probes} from './defect-probes.mjs';
const root=path.dirname(fileURLToPath(import.meta.url)),out=path.resolve(process.argv[2]||path.join(root,'defect-probes-proof'));await mkdir(out,{recursive:true});const results=[];
for(const mode of ['healthy','list_refresh','account_conflict','account_conflict_list','committed_refresh','comments_refresh','committed_refresh_comments','response_only','cancel_conflict']){
 const report=await probes({site:path.join(root,'fixture'),out:path.join(out,mode),env:{FRONTEND_FIXTURE_MODE:mode}});assert.equal(report.fatal,undefined);assert.equal(report.checks.find(r=>r.name==='healthy_comment_and_identity').status,'pass');
 for(const row of report.checks){const broken=['account_conflict','account_conflict_list'].includes(mode)&&row.name==='late_conflict_refresh_after_account_switch'||['committed_refresh','committed_refresh_comments'].includes(mode)&&row.name==='committed_comment_refresh_failure';assert.equal(row.status,broken?'fail':'pass',JSON.stringify({mode,row}));}
 const mutationRow=report.checks.find(r=>r.name==='committed_comment_refresh_failure');
 if(mode==='comments_refresh'||mode==='committed_refresh_comments')assert(mutationRow.evidence.injectedProjectReadPaths.includes('/api/projects/p1/comments'));
 if(mode==='response_only'){assert.equal(mutationRow.evidence.refreshStrategy,'no_refresh_response_acknowledgment');assert.equal(mutationRow.evidence.injectedProjectReadPaths.length,0);}
 if(mode==='cancel_conflict')assert(report.checks.find(r=>r.name==='late_conflict_refresh_after_account_switch').evidence.canceledProjectReads.length>0,'actual canceled request must be recorded');
 results.push({mode,checks:report.checks});console.log(JSON.stringify({mode,passed:report.passed,failed:report.failed}));
}
await writeFile(path.join(out,'regression.json'),JSON.stringify({status:'pass',scored:false,results},null,2));

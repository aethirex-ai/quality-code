"""Repeat-safe retained-session recovery. Requires independent proof before entry.
No product reset, no native phase/global/round ceiling, no acceptance waiver.
"""
import copy,hashlib,itertools,json,os,select,subprocess,sys,time
from pathlib import Path
ROOT=Path(os.environ.get('SERVICEFLOW_BENCHMARK_ROOT',str(Path(__file__).resolve().parent))).resolve()
sys.path.insert(0,str(ROOT))
import run
from phase_collect import source_hashes
from collect import private_credential_path


def independent_gate():
    proof=Path(os.environ.get('SERVICEFLOW_AMENDMENT2_AUDIT',str(ROOT/'controller-amendment2-entry-proof.json')))
    value=json.loads(proof.read_text())
    if value.get('verdict')!='PASS' or value.get('controller_sha256')!=run.digest(Path(__file__)):
        raise RuntimeError('Amendment2 independent proof missing PASS for exact v2 controller SHA256')


def continuation(condition):
    if condition not in ('single','adaptive'):raise ValueError('Unknown condition')
    protocol=run.runtime_protocol(json.loads((ROOT/'protocol.json').read_text()))
    directory=ROOT/'runs'/condition;site=directory/'site';path=directory/'metadata.json'
    meta=json.loads(path.read_text())
    if not meta.get('end_unix') or any(p.get('state')!='completed' for p in meta['phases']):
        raise RuntimeError('Only inactive original/recovery segments with every native phase completed can continue')
    if meta['state']=='PASS':return meta
    run.verify_freeze(protocol,site)
    current=source_hashes(site)
    expected={p:h for p,h in meta['final_source_sha256'].items() if not private_credential_path(p)}
    if current!=expected:raise RuntimeError('Product source changed during controller interruption')
    # Exclusive archives preserve all earlier metadata, including v1 archives.
    for number in itertools.count(1):
        prior=directory/('metadata-before-controller-continuation-v2-%03d.json'%number)
        try:
            with prior.open('xb') as stream:stream.write(path.read_bytes())
            break
        except FileExistsError:continue
    old_active=meta.get('active_controller_elapsed_seconds',meta['elapsed_seconds'])
    old_end=meta['end_unix'];segment_start=time.monotonic();segment_wall=time.time()
    history=meta.setdefault('controller_continuations',[])
    if not history and meta.get('controller_continuation'):
        history.append(copy.deepcopy(meta['controller_continuation']))
    segment={'version':2,'number':number,'reason':'credential filename and canonical acceptance identity amendment',
             'prior_metadata_path':prior.name,'prior_metadata_sha256':run.digest(prior),'prior_end_unix':old_end,
             'prior_state':meta['state'],'prior_active_controller_elapsed_seconds':old_active,
             'start_unix':segment_wall,'orchestration_gap_seconds':max(0,segment_wall-old_end),
             'prior_protocol_sha256':meta.get('updated_protocol_sha256',meta.get('protocol_sha256')),
             'protocol_sha256':run.digest(ROOT/'protocol.json'),'overlap_possible':True}
    history.append(segment)
    meta.update(state='INCOMPLETE',end_unix=None,runner_error=None,updated_protocol_sha256=segment['protocol_sha256'])
    port=protocol['ports'][condition]
    env=run.isolated_environment(os.environ)
    env.update(PREVIEW_NODE=run.NODE,PREVIEW_PLAYWRIGHT_MODULE=run.PW,BENCHMARK_NODE=run.NODE,
               BENCHMARK_PLAYWRIGHT_IMPORT=run.PW,PORTAL_PORT=str(port),NPM_CONFIG_CACHE=str(site/'.npm-cache'))
    broker=None;log=None;failure=None
    def save():run.write_json(path,meta)
    def phase(prompt,role,resume=None):
        result,_=run.execute_phase(condition,site,directory,protocol,meta,None,prompt.encode(),role=role,
                                   number=len(meta['phases'])+1,resume=resume,env=env)
        if result['state']!='completed':raise RuntimeError('Retained '+role+' phase incomplete')
        run.verify_freeze(protocol,site)
        return result
    def repair(findings,label):
        target=directory/('repair-v2-%03d-%s-findings.json'%(number,label));run.write_json(target,findings)
        return phase('Continue this exact original builder session. Fix every reproduced product issue in '+str(target)+
            '. This report is raw independent reproduction evidence, not an accepted canonical verdict. Keep protected corpus unchanged. '
            'Add focused regressions, rerun relevant full/release/build/browser checks and generate a fresh audit packet. Join helpers and '
            'return audit-ready with gate pending. A NEW complete independent ServiceFlow audit is required; do not supply its verdict. '
            'No elapsed or round cap. Do not inspect the other condition.','builder',meta['builder_root'])
    def invalidate(audited,raw,value,error):
        audited.update(canonical_state='invalid_scope_metadata',canonical_error=str(error),
                       raw_verdict_sha256=run.digest(raw) if raw.is_file() else None)
        if isinstance(value,dict):audited['raw_verdict']=value.get('verdict')
        audited.pop('verdict',None)
        save()
    save()
    try:
        log=(directory/('preview-broker-continuation-v2-%03d.log'%number)).open('x')
        run.cleanup_bound_backend(site,port,tuple(protocol['backend_command_markers']))
        broker=subprocess.Popen([sys.executable,str(ROOT/'preview/broker.py'),'--workspace',str(site),'--port',str(port)],
                                stdout=subprocess.PIPE,stderr=log,text=True,env=env,start_new_session=True)
        if not select.select([broker.stdout],[],[],30)[0] or not json.loads(broker.stdout.readline()).get('ready'):
            raise RuntimeError('Preview readiness unavailable')
        if not meta.get('initial_ready_source_snapshot'):
            meta['initial_ready_source_snapshot']=run.freeze_source_bytes(site,directory/('snapshots/initial-corrected-inventory-v2-%03d'%number),current)
            meta['initial_ready_unix']=meta['phases'][0]['end_unix'];meta['initial_ready_elapsed_seconds']=meta['phases'][0]['elapsed_seconds']
        for audited in list(meta['phases']):
            if audited['role']!='auditor' or audited.get('verdict'):continue
            raw=directory/'phases'/('%02d-auditor'%audited['number'])/'final.txt'
            try:value=json.loads(raw.read_text())
            except (ValueError,OSError) as exc:
                audited.update(canonical_state='invalid_raw_report',canonical_error=str(exc));save()
                raise RuntimeError('Prior auditor report unavailable or malformed; retained without acceptance') from exc
            invalidate(audited,raw,value,audited.get('canonical_error','Prior canonical report invalid'))
            followed=[p for p in meta['phases'] if p['role']=='builder' and p['number']>audited['number']]
            if followed:
                audited['supplemental_delivery']={'state':'already_followed_by_builder','builder_phase':followed[0]['number']}
                save();continue
            if audited.get('supplemental_delivery',{}).get('state')=='delivered':continue
            if value.get('findings'):
                repaired=repair({'kind':'supplemental independent reproduced findings; canonical metadata invalid',
                    'source_sha256':run.digest(raw),'findings':value['findings'],'fresh_complete_independent_audit_required':True},
                    'supplemental-%02d'%audited['number'])
                audited['supplemental_delivery']={'state':'delivered','builder_phase':repaired['number']};save()
        for round_number in itertools.count(len(meta.get('source_snapshots',[]))+1):
            gates=run.fixed_gates(protocol,site,directory,round_number,None,env);meta.setdefault('fixed_gates',[]).append(gates)
            meta.setdefault('pre_audit_backend_cleanup',[]).append(run.cleanup_bound_backend(site,port,tuple(protocol['backend_command_markers'])))
            args=[str(site/'quality'),'audit-packet','--force','--criteria',protocol['audit_acceptance_criteria'],'--base',protocol['audit_scope_base']]
            result=subprocess.run(args,cwd=site,capture_output=True,text=True,timeout=60)
            if result.returncode:raise RuntimeError('Audit packet generation failed')
            packet=json.loads(result.stdout);packet_path=directory/('audit-%02d-packet.json'%round_number);run.write_json(packet_path,packet)
            before=source_hashes(site);snapshot_path=directory/('audit-%02d-source-hashes.json'%round_number);run.write_json(snapshot_path,before)
            meta.setdefault('source_snapshots',[]).append({'round':round_number,'sources_sha256':before})
            prompt=(ROOT/'AUDIT_PROMPT.txt').read_text()+'\nCanonical scope.base must be exactly: '+json.dumps(protocol['audit_scope_base'])+\
                '\nCanonical scope.acceptance_criteria must be exactly: '+json.dumps(protocol['audit_acceptance_criteria'])+\
                '\nRead complete unchanged ACCEPTANCE.md and BRIEF.md; canonical identity is a hash label, not a replacement of the product requirements.'+\
                '\nFresh full-scope audit packet: '+str(packet_path)+'\nParent source inventory: '+str(snapshot_path)+\
                '\nRaw structural gate reports (not functional verdicts): '+json.dumps([r['report_path'] for r in gates['reports']])+\
                '\nNo elapsed deadline or audit-round ceiling. This is a fresh complete ServiceFlow audit.'
            audited=phase(prompt,'auditor')
            if source_hashes(site)!=before:raise RuntimeError('Auditor changed product source')
            audit_dir=directory/'phases'/('%02d-auditor'%audited['number']);raw=audit_dir/'final.txt';value=None
            try:
                value=json.loads(raw.read_text())
                status=run.validate_verdict(value,site,before,dict(protocol,audit_required_files=packet['changed_files']))
            except (ValueError,TypeError,KeyError,OSError) as exc:
                invalidate(audited,raw,value,exc)
                raise RuntimeError('Current auditor canonical report invalid; raw report/phase retained, acceptance refused') from exc
            audited['verdict']=status;run.write_json(audit_dir/'verdict.json',value);save()
            if status=='PASS' and gates['accepted']:
                meta.update(state='PASS',accepted_source_sha256=before,accepted_gate_unix=time.time());break
            if status=='BLOCKED' or gates['tool_incomplete']:meta['state']='BLOCKED';break
            if not gates['accepted']:
                value['findings'].append({'id':'AUD-999','severity':'high','title':'Structural deliverable gate failed','file':None,'line':None,
                    'evidence':json.dumps(gates['reports']),'required_action':'Repair missing deliverables without lowering product gates.'})
            repair(value,'audit-%02d'%round_number)
    except BaseException as exc:
        failure=exc;meta.update(state='INCOMPLETE',runner_error=type(exc).__name__+': '+str(exc))
    finally:
        errors=[]
        try:
            final=source_hashes(site);meta['final_source_sha256']=final
            target=directory/'snapshots'/('continuation-v2-%03d-final-%03d'%(number,len(meta['phases'])))
            meta['final_source_snapshot']=run.freeze_source_bytes(site,target,final)
            meta['final_source_snapshot_path']=str(target.relative_to(directory))
            if meta['state']=='PASS' and final!=meta['accepted_source_sha256']:raise RuntimeError('Accepted source changed')
        except Exception as exc:errors.append('snapshot: '+str(exc))
        try:meta['backend_cleanup']=run.cleanup_bound_backend(site,port,tuple(protocol['backend_command_markers']))
        except Exception as exc:errors.append('backend: '+str(exc))
        if broker is not None:
            try:run.terminate_group(broker)
            except Exception as exc:errors.append('preview: '+str(exc))
            broker.stdout.close()
        if log is not None:log.close()
        end=time.time();elapsed=time.monotonic()-segment_start
        segment.update(end_unix=end,monotonic_seconds=elapsed,state=meta['state'],cleanup_errors=errors)
        meta.update(end_unix=end,elapsed_seconds=end-meta['start_unix'],cleanup_errors=errors,budget_exceeded=False,
                    active_controller_elapsed_seconds=old_active+elapsed,continuation_monotonic_seconds=elapsed)
        meta['elapsed_measurement_note']='Calendar elapsed includes every interruption gap; active_controller_elapsed_seconds accumulates original and all continuation monotonic intervals only. Gaps/overlap retained; prevent unqualified causal speed inference.'
        if errors:meta['state']='INCOMPLETE';segment['state']='INCOMPLETE'
        save();print(json.dumps({'condition':condition,'state':meta['state'],'calendar_seconds':meta['elapsed_seconds'],
             'active_controller_seconds':meta['active_controller_elapsed_seconds'],'segment':number,'error':meta.get('runner_error')}),flush=True)
    if failure:raise failure
    return meta


if __name__=='__main__':
    independent_gate()
    continuation(sys.argv[1])

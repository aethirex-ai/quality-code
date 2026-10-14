"""Continue retained native ServiceFlow sessions after disclosed controller faults.
No implementation reset, no stage/global/audit ceiling, no acceptance waiver.
"""
import json,os,sys,time,subprocess,select,itertools,hashlib
from pathlib import Path
ROOT=Path(os.environ.get('SERVICEFLOW_BENCHMARK_ROOT', Path(__file__).resolve().parent)).resolve()
os.environ.setdefault('PYTHONDONTWRITEBYTECODE','1')
sys.path.insert(0,str(ROOT));import run
from phase_collect import source_hashes

def independent_gate():
    """Historical native approval cannot authorize adapted portable bytes."""
    proof_path=Path(os.environ.get('SERVICEFLOW_AMENDMENT_AUDIT', ROOT/'controller-amendment-portable-proof.json'))
    try:
        proof=json.loads(proof_path.read_text())
    except (OSError,ValueError) as exc:
        raise RuntimeError('Portable continuation proof unavailable or malformed') from exc
    if not isinstance(proof,dict) or proof.get('verdict')!='PASS' or proof.get('controller_sha256')!=run.digest(Path(__file__)):
        raise RuntimeError('Portable continuation proof must PASS this exact controller SHA256')

def continuation(condition):
    protocol=run.runtime_protocol(json.loads((ROOT/'protocol.json').read_text()));directory=ROOT/'runs'/condition;site=directory/'site';path=directory/'metadata.json'
    meta=json.loads(path.read_text())
    if not meta.get('end_unix')or any(p['state']=='running'for p in meta['phases']):raise RuntimeError('Original controller still active')
    if meta['state']=='PASS':return meta
    if any(p['state']!='completed'for p in meta['phases']):raise RuntimeError('Only completed retained native phases can be continued by this controller')
    prior=directory/'metadata-before-controller-continuation.json'
    if prior.exists():raise RuntimeError('Refuse blind duplicate continuation')
    prior.write_bytes(path.read_bytes());run.verify_freeze(protocol,site)
    current=source_hashes(site);expected={p:h for p,h in meta['final_source_sha256'].items()if Path(p).name!='.auth-secret'}
    if current!=expected:raise RuntimeError('Product source changed during controller interruption')
    old_elapsed=meta['elapsed_seconds'];old_end=meta['end_unix'];segment_start=time.monotonic();segment_wall=time.time();gap=max(0,segment_wall-old_end)
    meta.update(state='INCOMPLETE',end_unix=None,runner_error=None)
    meta['controller_continuation']={'reason':'runtime-secret inventory and formatter-scope amendment','prior_metadata_sha256':hashlib.sha256(prior.read_bytes()).hexdigest(),'start_unix':segment_wall,'orchestration_gap_seconds':gap,'prior_monotonic_elapsed_seconds':old_elapsed,'overlap_possible':True,'prior_errors_retained_in':prior.name}
    meta['updated_protocol_sha256']=run.digest(ROOT/'protocol.json');port=protocol['ports'][condition]
    env=run.isolated_environment(os.environ);env.update(PREVIEW_NODE=run.NODE,PREVIEW_PLAYWRIGHT_MODULE=run.PW,BENCHMARK_NODE=run.NODE,BENCHMARK_PLAYWRIGHT_IMPORT=run.PW,PORTAL_PORT=str(port),NPM_CONFIG_CACHE=str(site/'.npm-cache'))
    broker=None;log=(directory/'preview-broker-continuation.log').open('w');failure=None
    def save():run.write_json(path,meta)
    def phase(prompt,role,resume=None):
        result,_=run.execute_phase(condition,site,directory,protocol,meta,None,prompt.encode(),role=role,number=len(meta['phases'])+1,resume=resume,env=env)
        if result['state']!='completed':raise RuntimeError('Retained '+role+' phase incomplete')
        run.verify_freeze(protocol,site);return result
    def repair(findings,label):
        target=directory/('repair-'+label+'-findings.json');run.write_json(target,findings)
        phase('Continue this exact original builder session. Fix every reproduced product issue in '+str(target)+'. This report is raw independent reproduction evidence, not an accepted canonical verdict. Keep protected corpus unchanged. Add focused regressions, rerun relevant full/release/build/browser checks and generate a fresh audit packet. Join helpers and return audit-ready with gate pending. A NEW complete independent ServiceFlow audit is required; do not supply its verdict. No elapsed or round cap. Do not inspect the other condition.', 'builder',meta['builder_root'])
    try:
        run.cleanup_bound_backend(site,port,tuple(protocol['backend_command_markers']))
        broker=subprocess.Popen([sys.executable,str(ROOT/'preview/broker.py'),'--workspace',str(site),'--port',str(port)],stdout=subprocess.PIPE,stderr=log,text=True,env=env,start_new_session=True)
        if not select.select([broker.stdout],[],[],30)[0]or not json.loads(broker.stdout.readline()).get('ready'):raise RuntimeError('Preview readiness unavailable')
        if not meta.get('initial_ready_source_snapshot'):
            meta['initial_ready_source_snapshot']=run.freeze_source_bytes(site,directory/'snapshots/initial-corrected-inventory',current)
            meta['initial_ready_unix']=meta['phases'][0]['end_unix'];meta['initial_ready_elapsed_seconds']=meta['phases'][0]['elapsed_seconds']
        # Preserve invalid original JSON unchanged. Its demonstrated failures can
        # inform fixes, but it can never count as canonical app acceptance.
        invalid=[p for p in meta['phases']if p['role']=='auditor'and not p.get('verdict')]
        for p in invalid:
            raw=directory/'phases'/('%02d-auditor'%p['number'])/'final.txt';value=json.loads(raw.read_text())
            p['canonical_state']='invalid_scope_metadata';p['raw_verdict']=value.get('verdict')
            if value.get('findings'):
                repair({'kind':'supplemental independent reproduced findings; canonical metadata invalid','source_sha256':run.digest(raw),'findings':value['findings'],'fresh_complete_independent_audit_required':True},'supplemental-%02d'%p['number'])
        next_round=len(meta.get('source_snapshots',[]))+1
        for round_number in itertools.count(next_round):
            gates=run.fixed_gates(protocol,site,directory,round_number,None,env);meta.setdefault('fixed_gates',[]).append(gates)
            meta.setdefault('pre_audit_backend_cleanup',[]).append(run.cleanup_bound_backend(site,port,tuple(protocol['backend_command_markers'])))
            args=[str(site/'quality'),'audit-packet','--force','--criteria',protocol['audit_acceptance_criteria'],'--base',protocol['audit_scope_base']]
            result=subprocess.run(args,cwd=site,capture_output=True,text=True,timeout=60)
            if result.returncode:raise RuntimeError('Audit packet generation failed')
            packet=json.loads(result.stdout);packet_path=directory/('audit-%02d-packet.json'%round_number);run.write_json(packet_path,packet)
            before=source_hashes(site);snapshot_path=directory/('audit-%02d-source-hashes.json'%round_number);run.write_json(snapshot_path,before);meta.setdefault('source_snapshots',[]).append({'round':round_number,'sources_sha256':before})
            prompt=(ROOT/'AUDIT_PROMPT.txt').read_text()+'\nCanonical scope.base must be exactly: '+json.dumps(protocol['audit_scope_base'])+'\nCanonical scope.acceptance_criteria must be exactly: '+json.dumps(protocol['audit_acceptance_criteria'])+'\nFresh full-scope audit packet: '+str(packet_path)+'\nParent source inventory: '+str(snapshot_path)+'\nRaw structural gate reports (not functional verdicts): '+json.dumps([r['report_path']for r in gates['reports']])+'\nNo elapsed deadline or audit-round ceiling. This is a fresh complete ServiceFlow audit.'
            audited=phase(prompt,'auditor')
            if source_hashes(site)!=before:raise RuntimeError('Auditor changed product source')
            audit_dir=directory/'phases'/('%02d-auditor'%audited['number']);value=json.loads((audit_dir/'final.txt').read_text());validation=dict(protocol,audit_required_files=packet['changed_files']);status=run.validate_verdict(value,site,before,validation)
            audited['verdict']=status;run.write_json(audit_dir/'verdict.json',value);save()
            if status=='PASS'and gates['accepted']:
                meta.update(state='PASS',accepted_source_sha256=before,accepted_gate_unix=time.time());break
            if status=='BLOCKED'or gates['tool_incomplete']:meta['state']='BLOCKED';break
            if not gates['accepted']:value['findings'].append({'id':'AUD-999','severity':'high','title':'Structural deliverable gate failed','file':None,'line':None,'evidence':json.dumps(gates['reports']),'required_action':'Repair missing deliverables without lowering product gates.'})
            repair(value,'audit-%02d'%round_number)
    except BaseException as exc:
        failure=exc;meta.update(state='INCOMPLETE',runner_error=type(exc).__name__+': '+str(exc))
    finally:
        errors=[]
        try:
            final=source_hashes(site);meta['final_source_sha256']=final;target=directory/'snapshots'/('continuation-final-%02d'%len(meta['phases']));meta['final_source_snapshot']=run.freeze_source_bytes(site,target,final);meta['final_source_snapshot_path']=str(target.relative_to(directory))
            if meta['state']=='PASS'and final!=meta['accepted_source_sha256']:raise RuntimeError('Accepted source changed')
        except Exception as e:errors.append('snapshot: '+str(e))
        try:meta['backend_cleanup']=run.cleanup_bound_backend(site,port,tuple(protocol['backend_command_markers']))
        except Exception as e:errors.append('backend: '+str(e))
        if broker is not None:
            try:run.terminate_group(broker)
            except Exception as e:errors.append('preview: '+str(e))
            broker.stdout.close()
        log.close();end=time.time();segment=time.monotonic()-segment_start
        meta.update(end_unix=end,elapsed_seconds=end-meta['start_unix'],cleanup_errors=errors,budget_exceeded=False)
        meta['active_controller_elapsed_seconds']=old_elapsed+segment;meta['continuation_monotonic_seconds']=segment;meta['elapsed_measurement_note']='Calendar elapsed across controller interruption, including gap; original and continuation monotonic intervals separately retained. Benchmark overlap and infrastructure overhead prevent unqualified causal speed inference.'
        if errors:meta['state']='INCOMPLETE'
        save();print(json.dumps({'condition':condition,'state':meta['state'],'calendar_seconds':meta['elapsed_seconds'],'active_controller_seconds':meta['active_controller_elapsed_seconds'],'error':meta.get('runner_error')}),flush=True)
    if failure:raise failure
    return meta

def main():
    independent_gate()
    guard=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL) if Path('/usr/bin/caffeinate').is_file() else None
    try:
        condition=sys.argv[1]
        while not json.loads((ROOT/'runs'/condition/'metadata.json').read_text()).get('end_unix'):time.sleep(3)
        continuation(condition)
    finally:
        if guard is not None:guard.terminate();guard.wait(timeout=5)

if __name__=='__main__':
    main()

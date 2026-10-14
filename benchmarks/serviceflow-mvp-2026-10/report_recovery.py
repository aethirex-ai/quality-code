"""Exact independent auditor report-only correction; no product repair or reset."""
import argparse,copy,hashlib,itertools,json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(os.environ.get('SERVICEFLOW_BENCHMARK_ROOT',str(Path(__file__).resolve().parent))).resolve()
sys.path.insert(0,str(ROOT))
import run,phase_collect


def gate():
    path=Path(os.environ.get('SERVICEFLOW_REPORT_RECOVERY_AUDIT',str(ROOT/'report-recovery-publication-proof.json')))
    proof=json.loads(path.read_text())
    if proof.get('verdict')!='PASS' or proof.get('controller_sha256')!=run.digest(Path(__file__)):
        raise RuntimeError('Independent report-recovery proof must PASS exact controller SHA256')


def command(site,protocol,root,output):
    args=run.command('adaptive',site,protocol,role='auditor',output=output)
    # Retain matched model/effort, disabled delegation and exact-schema validation.
    pos=args.index('exec');args[pos+1:pos+1]=['resume',root]
    # Fresh run.command uses the writable implementation profile; correction is read-only.
    for index in range(len(args)-2,-1,-1):
        if args[index]=='-c' and (args[index+1].startswith('default_permissions=') or args[index+1].startswith('permissions.')):
            del args[index:index+2]
    pos=args.index('exec');args[pos:pos]=['-s','read-only']
    return args


def same_snapshot(left,right):
    return all(left.get(k)==right.get(k) for k in ['id','cumulative_usage','rollout_sha256','rollout_bytes','actual_models'])


def verified_usage(before,after,cli):
    old=phase_collect.validated_counter(before['cumulative_usage']);new=phase_collect.validated_counter(after['cumulative_usage'])
    delta={k:new[k]-old[k] for k in phase_collect.FIELDS};phase_collect.validated_counter(delta)
    if after['id']!=before['id'] or after['rollout_bytes']<before['rollout_bytes']:raise ValueError('Correction native root/truncation mismatch')
    required=('input_tokens','cached_input_tokens','output_tokens')
    if not isinstance(cli,dict) or any(type(cli.get(k)) is not int or cli[k]<0 for k in required):raise ValueError('Correction CLI usage missing/invalid')
    keys=[k for k in phase_collect.FIELDS if k in cli]
    if any(type(cli[k]) is not int for k in keys):raise ValueError('Correction CLI usage invalid type')
    if all(cli[k]==delta[k] for k in keys):basis='phase_increment'
    elif all(cli[k]==new[k] for k in keys):basis='root_cumulative'
    else:raise ValueError('Correction CLI/native counters mismatch')
    return new,delta,basis


def final_snapshot(directory,meta,current):
    target=directory/meta['final_source_snapshot_path']
    if not target.resolve().is_relative_to(directory.resolve()) or any(p.is_symlink() for p in [target,*target.parents]):raise RuntimeError('Unsafe final snapshot')
    manifest=target/'manifest.json';value=json.loads(manifest.read_text())
    if run.digest(manifest)!=meta['final_source_snapshot']['manifest_sha256'] or value['sources_sha256']!=current:raise RuntimeError('Final snapshot manifest mismatch')
    for relative,expected in current.items():
        path=Path(relative)
        if path.is_absolute() or '..' in path.parts:raise RuntimeError('Unsafe snapshot source path')
        file=target/'sources'/path
        if any(p.is_symlink() for p in [file,*file.parents]) or run.digest(file)!=expected:raise RuntimeError('Final snapshot source mismatch')


STARTUP_ERROR = 'Error: failed to initialize in-process app-server client: config defines `[permissions]` profiles but does not set `default_permissions`'


def restore_startup_failure(directory,meta,audited):
    """Restore aggregate provenance only for the evidenced zero-work format001 startup failure."""
    corrections=audited.get('formatting_corrections',[])
    if len(corrections)!=1 or audited.get('state')!='invalid':raise RuntimeError('Retry is limited to the original zero-work startup failure')
    failed=corrections[0];target=directory/'phases/08-auditor/format-001'
    stored=json.loads((target/'metadata.json').read_text())
    if stored!=failed or failed.get('exit_code')!=1 or failed.get('state')!='invalid':raise RuntimeError('Failed startup metadata/exit mismatch')
    events=target/'events.jsonl';stderr=target/'stderr.log'
    if events.is_symlink() or stderr.is_symlink() or events.read_bytes()!=b'' or stderr.read_text().strip()!=STARTUP_ERROR:
        raise RuntimeError('Retry requires exact known startup error and empty events')
    original_file=target/'original-phase.json'
    if run.digest(original_file)!=failed.get('original_phase_sha256'):raise RuntimeError('Archived original phase changed')
    original=json.loads(original_file.read_text())
    if original.get('state')!='completed' or original.get('number')!=8 or original.get('role')!='auditor' or original.get('native_before') is not None or original.get('resume_root'):
        raise RuntimeError('Archived original phase is not fresh completed auditor')
    baseline=original['native_after']
    if not all(same_snapshot(baseline,value) for value in [failed.get('native_before',{}),failed.get('native_after',{}),audited.get('native_after',{})]):
        raise RuntimeError('Retry native counters/rollout grew or changed')
    phase_dir=directory/'phases/08-auditor'
    if run.digest(phase_dir/'final.txt')!=failed.get('original_report_sha256') or any(run.digest(phase_dir/n)!=h for n,h in failed['original_phase_files_sha256'].items()):
        raise RuntimeError('Original source report/phase evidence changed')
    restored=copy.deepcopy(original)
    restored.update(formatting_corrections=copy.deepcopy(corrections),elapsed_seconds=audited['elapsed_seconds'],end_unix=audited['end_unix'])
    meta['phases'][-1]=restored
    meta['report_retry_restore']={'basis':'exact config startup error, exit1, empty events and no native counter/rollout growth',
        'failed_segment_path':str(target.relative_to(directory)),'original_phase_sha256':run.digest(original_file),
        'failed_segment_metadata_sha256':run.digest(target/'metadata.json'),'empty_events_sha256':run.digest(events),
        'prior_aggregate_phase_state':audited['state'],'prior_aggregate_cli_usage':audited.get('cli_usage'),
        'restored_cli_usage':restored['cli_usage'],'failed_elapsed_retained':True}
    return restored


def preflight():
    protocol=run.runtime_protocol(json.loads((ROOT/'protocol.json').read_text()));directory=ROOT/'runs/adaptive';site=directory/'site'
    meta=json.loads((directory/'metadata.json').read_text())
    if meta.get('state')=='PASS':raise RuntimeError('Condition already accepted; refuse duplicate report correction')
    if not meta.get('end_unix') or any(p.get('state')!='completed' for p in meta['phases'][:-1]):raise RuntimeError('All native phases must be complete and condition ended')
    audited=meta['phases'][-1]
    if audited.get('state')=='invalid':audited=restore_startup_failure(directory,meta,audited)
    if audited.get('state')!='completed':raise RuntimeError('All native phases must be complete and condition ended')
    if audited.get('number')!=8 or audited.get('role')!='auditor' or audited.get('resume_root') or audited.get('native_before') is not None:raise RuntimeError('Target must be original fresh phase8 independent auditor')
    root=audited.get('root_id')
    if not run.valid_id(root) or root==meta.get('builder_root') or meta.get('auditor_roots',[]).count(root)!=1 or any(p.get('root_id')==root for p in meta['phases'][:-1]):raise RuntimeError('Original auditor independence not proven')
    if protocol.get('root_reasoning_effort')!='high' or audited['native_after'].get('actual_models')!=[protocol['root_model']]:raise RuntimeError('Matched model/high evidence missing')
    run.verify_freeze(protocol,site)
    current=phase_collect.source_hashes(site)
    latest=meta['source_snapshots'][-1];round_number=latest['round']
    recorded=json.loads((directory/('audit-%02d-source-hashes.json'%round_number)).read_text())
    if current!=meta['final_source_sha256'] or current!=latest['sources_sha256'] or current!=recorded:raise RuntimeError('Current/final/phase8 audited source mismatch')
    final_snapshot(directory,meta,current)
    packet=json.loads((directory/('audit-%02d-packet.json'%round_number)).read_text())
    original_dir=directory/'phases/08-auditor';raw=original_dir/'final.txt';value=json.loads(raw.read_text())
    if value.get('verdict')!='PASS' or value.get('findings') or value.get('untested') or value.get('worktree_unchanged') is not True:raise RuntimeError('Original report is not bounded report-format PASS candidate')
    invalid=[check for check in value['checks'] if check.get('status')!='pass' or check.get('exit_code')!=0]
    if len(invalid)!=1 or invalid[0].get('command')!=['npm','run','benchmark:start'] or invalid[0].get('status')!='pass' or invalid[0].get('exit_code')!=130:raise RuntimeError('Original report differs from explicit server-cleanup formatting case')
    # Verify every other strict contract by testing a private in-memory copy only.
    candidate=copy.deepcopy(value);candidate['checks'].remove(next(c for c in candidate['checks'] if c==invalid[0]))
    run.validate_verdict(candidate,site,current,dict(protocol,audit_required_files=packet['changed_files']))
    gates=meta.get('fixed_gates',[])
    if not gates or any(not g.get('accepted') or g.get('tool_incomplete') for g in gates):raise RuntimeError('Prior structural gates not completely accepted')
    before=run.root_snapshot(protocol['sessions_dir'],root,site)
    if not same_snapshot(before,audited['native_after']):raise RuntimeError('Original auditor native snapshot changed outside owned turn')
    _,_,flags=phase_collect.reconcile_phases(meta['phases'])
    if flags:raise RuntimeError('Prior native phase accounting not reconciled: '+','.join(sorted(flags)))
    return protocol,directory,site,meta,audited,current,packet,before


def recover():
    protocol,directory,site,meta,audited,current,packet,before=preflight()
    phase_dir=directory/'phases/08-auditor'
    lock=directory/'.report-recovery.lock'
    with lock.open('x') as handle:handle.write(str(os.getpid()))
    try:return correction(protocol,directory,site,meta,audited,current,packet,before,phase_dir)
    finally:lock.unlink()


def correction(protocol,directory,site,meta,audited,current,packet,before,phase_dir):
    for number in itertools.count(1):
        target=phase_dir/('format-%03d'%number)
        try:target.mkdir();break
        except FileExistsError:continue
    original=copy.deepcopy(audited)
    (target/'metadata-before.json').write_bytes((directory/'metadata.json').read_bytes())
    run.write_json(target/'original-phase.json',original)
    immutable={p.name:run.digest(p) for p in phase_dir.iterdir() if p.is_file()}
    if (phase_dir/'metadata.json').is_file():(target/'original-phase-file.json').write_bytes((phase_dir/'metadata.json').read_bytes())
    start_wall=time.time();start_mono=time.monotonic();old_active=meta.get('active_controller_elapsed_seconds',meta['elapsed_seconds'])
    record={'number':number,'state':'running','original_phase_sha256':run.digest(target/'original-phase.json'),
      'original_report_sha256':run.digest(phase_dir/'final.txt'),'original_phase_files_sha256':immutable,
      'native_before':before,'prior_condition_end_unix':meta['end_unix'],'start_unix':start_wall,
      'orchestration_gap_seconds':max(0,start_wall-meta['end_unix']),'prior_active_controller_elapsed_seconds':old_active,
      'protocol_sha256':run.digest(ROOT/'protocol.json'),'correction_scope':'same independent auditor, report format only',
      'original_native_elapsed_seconds':original['elapsed_seconds'],
      'prior_canonical_metadata':{k:original[k] for k in ('canonical_state','canonical_error','raw_verdict','raw_verdict_sha256') if k in original}}
    audited.setdefault('formatting_corrections',[]).append(record)
    meta.setdefault('report_recovery_segments',[]).append({'path':str(target.relative_to(directory)),**copy.deepcopy(record)})
    segment=meta['report_recovery_segments'][-1]
    audited.update(state='running');meta.update(state='INCOMPLETE',end_unix=None,runner_error=None)
    args=command(site,protocol,before['id'],target/'final.txt');record['command']=args
    prompt=('Correct ONLY your own phase8 canonical report. You are the SAME original independent auditor, not the builder. '
      'Read your retained evidence and original report '+str(phase_dir/'final.txt')+'. Do not change app/product source or run a new full audit. '
      'Preserve the factual npm run benchmark:start exit130 and deliberate Ctrl-C cleanup evidence. Expected server shutdown is resource cleanup, '
      'not a passing test assertion. Verify actual successful assertion commands from your own retained evidence; never invent exit0 or hide any '
      'failed required check. Return FAIL/BLOCKED if evidence is uncertain or a required check failed. Output exactly the nine-field canonical '
      'report with the SAME complete source scope and required full/release evidence. No delegation. No app/source writes. '
      'The original raw report remains immutable; write only the final response through CLI output. '
      'Canonical scope.base='+json.dumps(protocol['audit_scope_base'])+'; scope.acceptance_criteria='+json.dumps(protocol['audit_acceptance_criteria'])+
      '; source inventory='+json.dumps(current)+'; required files='+json.dumps(packet['changed_files'])+'. No elapsed or round ceiling.').encode()
    run.write_json(directory/'metadata.json',meta);process=None;failure=None;after=None
    try:
        with (target/'events.jsonl').open('wb') as out,(target/'stderr.log').open('wb') as err:
            process=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=out,stderr=err,cwd=site,env=run.isolated_environment(os.environ),start_new_session=True)
            try:process.communicate(input=prompt)
            finally:run.terminate_group(process)
        record['exit_code']=process.returncode
        observed,cli=run.parse_events(target/'events.jsonl');record.update(observed_root=observed,cli_usage=cli)
        after=run.root_snapshot(protocol['sessions_dir'],before['id'],site);record['native_after']=after
        if observed!=before['id']:raise RuntimeError('Correction resumed wrong native root')
        if after.get('actual_models')!=[protocol['root_model']]:raise RuntimeError('Correction actual model changed')
        cumulative,delta,basis=verified_usage(before,after,cli)
        record.update(verified_native_delta=delta,cli_counter_basis=basis,counters_verified=True)
        # Fresh original auditor phase becomes one evidenced aggregate cumulative root.
        audited.update(native_after=after,cli_usage=cumulative)
        if process.returncode!=0:raise RuntimeError('Correction native process nonzero exit')
        if phase_collect.source_hashes(site)!=current:raise RuntimeError('Auditor changed product source')
        run.verify_freeze(protocol,site);final_snapshot(directory,meta,current)
        if any(run.digest(phase_dir/n)!=h for n,h in immutable.items()):raise RuntimeError('Original phase evidence changed')
        value=json.loads((target/'final.txt').read_text())
        status=run.validate_verdict(value,site,current,dict(protocol,audit_required_files=packet['changed_files']))
        record.update(state='completed',verdict=status)
        audited.update(state='completed',verdict=status,canonical_state='validated_after_format_correction',canonical_report_path=str((target/'final.txt').relative_to(directory)))
        audited.pop('canonical_error',None)
        meta.update(state=status,report_recovery_accounting_complete=True)
        if status=='PASS':meta.update(accepted_source_sha256=current,accepted_gate_unix=time.time())
    except BaseException as exc:
        failure=exc;record.update(state='invalid',error=type(exc).__name__+': '+str(exc));audited.update(state='invalid')
        audited.pop('verdict',None)
        meta.update(state='INCOMPLETE',runner_error=record['error'],report_recovery_accounting_complete=False)
        # Capture authoritative target-root consumption even after event/parser/process failure.
        if after is None:
            try:after=run.root_snapshot(protocol['sessions_dir'],before['id'],site);record['native_after']=after
            except Exception as counter_error:record['counter_error']=str(counter_error)
        if after is not None:audited['native_after']=after
        if not record.get('counters_verified'):audited['cli_usage']=None
    finally:
        end=time.time();elapsed=time.monotonic()-start_mono
        record.update(end_unix=end,elapsed_seconds=elapsed,exit_code=process.returncode if process is not None else None)
        audited.update(end_unix=end,elapsed_seconds=original['elapsed_seconds']+elapsed)
        meta.update(end_unix=end,elapsed_seconds=end-meta['start_unix'],active_controller_elapsed_seconds=old_active+elapsed)
        segment.update(copy.deepcopy(record));meta['elapsed_measurement_note']='Calendar elapsed retains report-recovery gap; active time adds only new monotonic correction interval. Original phase files and raw report immutable; one original independent auditor root includes verified correction usage once.'
        run.write_json(target/'metadata.json',record);run.write_json(directory/'metadata.json',meta)
    if failure:raise failure
    return meta


if __name__=='__main__':
    gate();guard=None
    if shutil.which('caffeinate'):guard=subprocess.Popen(['caffeinate','-i','-w',str(os.getpid())],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:recover()
    finally:
        if guard is not None:guard.terminate();guard.wait()

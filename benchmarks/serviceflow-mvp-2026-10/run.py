"""Matched native builder sessions; shared time includes owned solver cleanup."""
import json,os,sys,time,signal,subprocess,select,socket,hashlib,itertools,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
NODE=os.environ.get('PREVIEW_NODE','node')
PW=os.environ.get('PREVIEW_PLAYWRIGHT_MODULE','playwright')
def runtime_protocol(protocol):
    """Resolve portable placeholders only for an explicitly requested new run."""
    value = dict(protocol)
    cli = os.environ.get('SERVICEFLOW_NATIVE_CLI', value.get('native_cli', 'codex'))
    discovered = shutil.which(cli)
    value['native_cli'] = str(Path(discovered or cli).expanduser().resolve())
    sessions = os.environ.get('SERVICEFLOW_SESSIONS_DIR', value.get('sessions_dir', ''))
    if sessions == '<set SERVICEFLOW_SESSIONS_DIR>':
        sessions = str(Path.home() / '.codex' / 'sessions')
    value['sessions_dir'] = str(Path(sessions).expanduser().resolve())
    return value

def terminate_group(process,grace=2):
 pgid=process.pid
 try:os.killpg(pgid,signal.SIGTERM)
 except ProcessLookupError:return
 until=time.monotonic()+grace
 while time.monotonic()<until:process.poll();time.sleep(min(.05,max(0,until-time.monotonic())))
 process.poll()  # Reap an exited leader before signaling remaining group members.
 try:os.killpg(pgid,signal.SIGKILL)
 except ProcessLookupError:pass
 except PermissionError:
  # Darwin can deny signaling a group that became zombie-only after poll.
  # Reap our exact leader and waive only a numerically absent/zombie group.
  process.poll()
  try:
   state=subprocess.run(['ps','-axo','pgid=,stat='],capture_output=True,text=True,timeout=1)
  except (OSError,subprocess.TimeoutExpired):raise
  rows=[line.split() for line in state.stdout.splitlines() if line.strip()]
  if state.returncode or not rows or any(len(row)!=2 or not row[0].isdigit() for row in rows):raise
  members=[row[1] for row in rows if row[0]==str(pgid)]
  if any(not value.startswith('Z') for value in members):raise
 try:process.wait(timeout=2)
 except subprocess.TimeoutExpired:raise RuntimeError('Owned process leader did not exit')
def cleanup_bound_backend(site,port,command_markers=("server.py",)):
 """Signal only assigned-port listeners proven inside this unique app tree."""
 site=site.resolve();notes=[]
 found=subprocess.run(['lsof','-nP','-iTCP:'+str(port),'-sTCP:LISTEN','-t'],capture_output=True,text=True,timeout=2)
 if found.returncode not in (0,1):raise RuntimeError('Cannot inspect assigned listener')
 def owned(pid,identity):
  if identity is None or kernel_process_identity(pid)!=identity:return False
  current=subprocess.run(['lsof','-nP','-a','-p',str(pid),'-iTCP:'+str(port),'-sTCP:LISTEN','-t'],capture_output=True,text=True,timeout=2)
  cwd=subprocess.run(['lsof','-a','-p',str(pid),'-d','cwd','-Fn'],capture_output=True,text=True,timeout=2)
  cmd=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True,timeout=2)
  dirs=[Path(line[1:]).resolve() for line in cwd.stdout.splitlines() if line.startswith('n')]
  return (current.returncode==0 and str(pid)in current.stdout.split() and cwd.returncode==0 and cmd.returncode==0
          and any(path.is_relative_to(site)for path in dirs)and any(marker in cmd.stdout for marker in command_markers)
          and kernel_process_identity(pid)==identity)
 for token in set(found.stdout.split()):
  if not token.isdigit():raise RuntimeError('Malformed assigned listener inventory')
  pid=int(token);identity=kernel_process_identity(pid)
  if not owned(pid,identity):
   notes.append({'listener_pid':pid,'action':'not_signaled','reason':'ownership not proven'});continue
  try:os.kill(pid,signal.SIGTERM)
  except ProcessLookupError:continue
  deadline=time.monotonic()+1
  while time.monotonic()<deadline and kernel_process_identity(pid)==identity:time.sleep(.05)
  if kernel_process_identity(pid)==identity:
   # Same creation identity and app cwd remain required. If socket already
   # closed, the owned process may still be exiting; never target a reused PID.
   cwd=subprocess.run(['lsof','-a','-p',str(pid),'-d','cwd','-Fn'],capture_output=True,text=True,timeout=2)
   dirs=[Path(line[1:]).resolve()for line in cwd.stdout.splitlines()if line.startswith('n')]
   if not any(path.is_relative_to(site)for path in dirs):raise RuntimeError('Owned process cwd changed before cleanup')
   if kernel_process_identity(pid)==identity:
    try:os.kill(pid,signal.SIGKILL)
    except ProcessLookupError:pass
  notes.append({'listener_pid':pid,'action':'owned backend terminated'})
 remaining=subprocess.run(['lsof','-nP','-iTCP:'+str(port),'-sTCP:LISTEN','-t'],capture_output=True,text=True,timeout=2)
 if remaining.returncode not in (0,1):raise RuntimeError('Cannot verify assigned listener cleanup')
 if remaining.stdout.strip():raise RuntimeError('Assigned port listener remains; no unproven process was signaled')
 return notes



def command(condition, site, protocol, *, role='builder', resume=None, output=None):
    """Global controls precede exec; resumes name the exact original root."""
    if condition not in ('single', 'adaptive') or role not in ('builder', 'auditor'):
        raise ValueError('Unknown condition or role')
    if resume is not None and (role != 'builder' or not valid_id(resume)):
        raise ValueError('Only exact builder root resumes are permitted')
    cli = protocol['native_cli']
    if not Path(cli).is_absolute():
        raise ValueError('Native CLI must be an absolute discovered path')
    delegates = condition == 'adaptive' and role == 'builder'
    args = [cli, '--no-daemon', '-a', 'never',
            '--enable', 'model_catalog_in_context', '-m', protocol['root_model'],
            '-c', 'model_reasoning_effort=' + json.dumps(protocol['root_reasoning_effort']),
            '-c', 'features.apps=false',
            '-c', 'agents.max_concurrent_threads_per_session=' + str(protocol['native_helper_cap']),
            '-c', 'default_permissions="portal-local"',
            '-c', 'permissions.portal-local.extends=":workspace"',
            '-c', 'permissions.portal-local.network.enabled=true',
            '-c', 'permissions.portal-local.network.allow_local_binding=true',
            '-c', 'permissions.portal-local.network.domains={' + ','.join(json.dumps(domain)+'="allow"' for domain in protocol.get('network_allow_domains', ['127.0.0.1', 'localhost'])) + '}',
            '-c', 'features.network_proxy=true']
    for feature in ('multi_agent_v2', 'multi_agent'):
        args += ['--enable' if delegates else '--disable', feature]
    args += ['-c', 'agents.enabled=' + ('true' if delegates else 'false'), 'exec']
    if resume:
        args += ['resume', resume]
    args += ['--ignore-user-config', '--strict-config', '--json']
    if role == 'auditor':
        args += ['--output-schema', str(ROOT / 'audit-output-schema.json')]
    if output:
        args += ['-o', str(output)]
    return args + ['-']


def valid_id(value):
    import re
    return isinstance(value, str) and bool(re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', value))


def digest(path):
    if path.is_symlink() or not path.is_file():
        raise RuntimeError('Expected regular protected file: ' + str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def verify_freeze(protocol, site, *, initial=False):
    required = set(protocol.get('required_frozen_sources', {'run.py', 'phase_collect.py', 'telemetry.py', 'prices.json',
                'judge/backend/evaluate.py', 'judge/frontend/evaluate.mjs',
                'preview/broker.py', 'preview/render.mjs', 'APP_PROMPT.txt',
                'AUDIT_PROMPT.txt', 'audit-output-schema.json'}))
    frozen = protocol.get('frozen_sources_sha256', {})
    if not required.issubset(frozen):
        raise RuntimeError('Incomplete measured-source freeze')
    for relative, expected in frozen.items():
        if digest(ROOT / relative) != expected:
            raise RuntimeError('Frozen source changed: ' + relative)
    corpus = dict(protocol['fixture_sha256'])
    if initial:
        corpus.update(protocol.get('initial_fixture_sha256', {}))
    for relative, expected in corpus.items():
        for base in (ROOT / 'fixture', site):
            if digest(base / relative) != expected:
                raise RuntimeError('Protected common corpus changed: ' + str(base / relative))
    if protocol.get('required_critical_route') or protocol.get('audit_required_risk') == 'critical':
        import tomllib
        quality = tomllib.loads((site / '.quality/quality.toml').read_text())
        routes = quality.get('areas', quality.get('routes', []))
        route_name = protocol.get('required_critical_route', 'auth-and-state')
        route = next((r for r in routes if r.get('name') == route_name), None)
        if not route or route.get('risk') != 'critical' or not {'full', 'release'}.issubset(route.get('required_profiles', [])):
            raise RuntimeError('Required critical auth/state route downgraded')
        import fnmatch
        if not all(any(fnmatch.fnmatchcase(path, pattern) for pattern in route.get('paths', [])) for path in protocol.get('critical_implementation_paths', ('server.py', 'public/index.html'))):
            raise RuntimeError('Critical auth/state route no longer covers implementation')
        if quality.get('audit', {}).get('independent_audit_min_risk') not in ('high', 'critical'):
            raise RuntimeError('Independent audit threshold changed')
    if initial and any((site / path).exists() for path in protocol.get('initial_forbidden_paths', ('server.py', 'public'))):
        raise RuntimeError('App implementation already exists before timing')
    prompt = (ROOT / 'APP_PROMPT.txt').read_bytes()
    if hashlib.sha256(prompt).hexdigest() != protocol['prompt_sha256']:
        raise RuntimeError('Common prompt changed')
    if (site / 'APP_PROMPT.txt').read_bytes() != prompt:
        raise RuntimeError('Workspace prompt mismatch')


def session_index(directory):
    """Read metadata only, never unrelated transcript bodies."""
    out = {}
    for path in Path(directory).rglob('*.jsonl'):
        if path.is_symlink():
            continue
        try:
            with path.open() as stream:
                row = json.loads(stream.readline())
            meta = row.get('payload', {})
            if row.get('type') == 'session_meta' and valid_id(meta.get('id')):
                out.setdefault(meta['id'], []).append((path, meta))
        except (OSError, ValueError, AttributeError):
            continue
    return out


def root_snapshot(sessions_dir, root, site):
    rows = session_index(sessions_dir).get(root, [])
    if len(rows) != 1:
        raise RuntimeError('Native root rollout missing or duplicated')
    path, meta = rows[0]
    if Path(meta.get('cwd', '')).resolve() != site.resolve():
        raise RuntimeError('Native root workspace mismatch')
    # Only selected, proven owned rollout bodies may now be inspected.
    counters = None
    models = set()
    for line in path.read_text().splitlines():
        row = json.loads(line)
        payload = row.get('payload', {})
        if row.get('type') == 'turn_context' and isinstance(payload.get('model'), str):
            models.add(payload['model'])
        if row.get('type') == 'event_msg' and payload.get('type') == 'token_count':
            info = payload.get('info')
            if isinstance(info, dict) and isinstance(info.get('total_token_usage'), dict):
                counters = info['total_token_usage']
    return {'id': root, 'session_meta': meta, 'rollout_sha256': digest(path),
            'rollout_bytes': path.stat().st_size, 'cumulative_usage': counters,
            'actual_models': sorted(models)}


def parse_events(path):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    roots = [r.get('thread_id') for r in rows if r.get('type') == 'thread.started']
    ends = [r.get('usage') for r in rows if r.get('type') == 'turn.completed']
    if len(roots) != 1 or not valid_id(roots[0]):
        raise RuntimeError('Expected exactly one explicit native CLI root')
    return roots[0], ends[0] if len(ends) == 1 and isinstance(ends[0], dict) else None


def uncapped(protocol):
    return protocol.get('completion_mode') == 'uncapped'


def audit_rounds(protocol):
    return itertools.count(1) if uncapped(protocol) else range(1, protocol['max_audit_rounds'] + 1)


def remaining_seconds(deadline):
    return None if deadline is None else deadline - time.monotonic()


def remaining_prompt(deadline):
    return ('\nCompletion is uncapped: continue until independent acceptance; no elapsed deadline or audit-round ceiling.'
            if deadline is None else '\nGlobal remaining seconds: ' + str(int(remaining_seconds(deadline))))


def tool_timeout(protocol, deadline, maximum):
    # Fixed deterministic tools have technical bounds, never agent-work deadlines.
    if uncapped(protocol):
        return maximum
    return max(.01, min(maximum, remaining_seconds(deadline)-protocol['cleanup_reserve_seconds']))


def phase_limit(protocol, role, initial, remaining):
    if uncapped(protocol):
        return None
    reserve = protocol['cleanup_reserve_seconds']
    limit = min(remaining - reserve, protocol.get('audit_phase_cap_seconds', 1200) if role == 'auditor' else protocol.get('repair_phase_cap_seconds', 900))
    if initial:
        limit = min(remaining - reserve, protocol['initial_builder_cap_seconds'],
                    remaining - protocol['gate_reserve_seconds'])
    return max(0, limit)


def execute_phase(condition, site, directory, protocol, meta, deadline, prompt,
                  *, role, number, resume=None, env=None):
    before = root_snapshot(protocol['sessions_dir'], resume, site) if resume else None
    foreign = set(session_index(protocol['sessions_dir']))
    phase_dir = directory / 'phases' / ('%02d-%s' % (number, role))
    phase_dir.mkdir(parents=True, exist_ok=False)
    args = command(condition, site, protocol, role=role, resume=resume,
                   output=phase_dir / 'final.txt')
    limit = phase_limit(protocol, role, number == 1, remaining_seconds(deadline))
    if limit is not None and limit <= 0:
        raise TimeoutError('Global budget has no phase allowance')
    phase = {'number': number, 'role': role, 'resume_root': resume,
             'start_unix': time.time(), 'command': args, 'allowance_seconds': limit,
             'state': 'running', 'native_before': before}
    meta['phases'].append(phase)
    write_json(directory / 'metadata.json', meta)
    start = time.monotonic()
    process = None
    try:
        with (phase_dir / 'events.jsonl').open('wb') as out, (phase_dir / 'stderr.log').open('wb') as err:
            process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                       cwd=site, env=env, start_new_session=True)
            # Uncapped agent work has no elapsed timeout; tool-level health/request bounds stay separate.
            try:
                process.communicate(input=prompt) if limit is None else process.communicate(input=prompt, timeout=limit)
                phase['state'] = 'exited'
            except subprocess.TimeoutExpired:
                phase['state'] = 'timed_out'
            finally:
                terminate_group(process, grace=2 if deadline is None else min(2, max(0, deadline-time.monotonic())))
                phase['exit_code'] = process.returncode
        root, usage = parse_events(phase_dir / 'events.jsonl')
        if resume and root != resume:
            raise RuntimeError('CLI resumed a different root')
        if not resume and root in foreign:
            raise RuntimeError('Fresh native phase reused an already-started root')
        if root in meta.get('auditor_roots', []) or (role == 'auditor' and root == meta.get('builder_root')):
            raise RuntimeError('Auditor/builder independence violated')
        phase.update(root_id=root, cli_usage=usage,
                     native_after=root_snapshot(protocol['sessions_dir'], root, site))
        if role == 'builder':
            if meta.get('builder_root') and meta['builder_root'] != root:
                raise RuntimeError('Builder restarted instead of resumed')
            meta['builder_root'] = root
        else:
            meta.setdefault('auditor_roots', []).append(root)
        if phase['state'] == 'exited' and phase['exit_code'] == 0 and usage is not None:
            phase['state'] = 'completed'
    except BaseException as exc:
        phase['error'] = type(exc).__name__ + ': ' + str(exc)
        if phase['state'] != 'timed_out':
            phase['state'] = 'invalid'
        raise
    finally:
        phase.update(end_unix=time.time(), elapsed_seconds=time.monotonic()-start)
        write_json(phase_dir / 'metadata.json', phase)
        write_json(directory / 'metadata.json', meta)
    return phase, phase_dir


def validate_verdict(value, site, snapshot, protocol=None):
    """Canonical nine-field schema plus strict acceptance-only gate rules."""
    import re
    protocol = protocol or {}
    required = {'schema_version', 'verdict', 'scope', 'risk', 'checks', 'findings',
                'untested', 'residual_risk', 'worktree_unchanged'}
    if not isinstance(value, dict) or set(value) != required or value['schema_version'] != 1:
        raise ValueError('Invalid canonical independent verdict fields')
    if value['verdict'] not in ('PASS', 'FAIL', 'BLOCKED') or value['risk'] not in ('critical', 'high', 'normal', 'low'):
        raise ValueError('Invalid independent verdict/risk')
    if protocol.get('audit_required_risk') and value['risk'] != protocol['audit_required_risk']:
        raise ValueError('Independent audit risk differs from protected route')
    scope = value['scope']
    if not isinstance(scope, dict) or set(scope) != {'base', 'changed_files', 'acceptance_criteria'}:
        raise ValueError('Independent scope missing')
    if not all(isinstance(scope[k], str) and scope[k] for k in ('base', 'acceptance_criteria')):
        raise ValueError('Independent scope strings missing')
    files = scope['changed_files']
    if not isinstance(files, list) or not files or not all(isinstance(f, str) and f for f in files) or len(set(files)) != len(files):
        raise ValueError('Invalid independent scope file list')
    product = set(snapshot) if protocol.get('audit_product_scope') == 'all-source' else {f for f in snapshot if f == 'server.py' or f.startswith('public/')}
    if not product or not (product | set(protocol.get('audit_required_files', []))).issubset(set(files)):
        raise ValueError('Independent audit omitted product implementation scope')
    for key, field in (('audit_scope_base', 'base'), ('audit_acceptance_criteria', 'acceptance_criteria')):
        if key in protocol and scope[field] != protocol[key]:
            raise ValueError('Independent scope differs from protocol')
    if (type(value['worktree_unchanged']) is not bool or not isinstance(value['untested'], list)
            or not all(isinstance(v, str) for v in value['untested'])
            or not isinstance(value['residual_risk'], str) or not value['residual_risk']):
        raise ValueError('Invalid independent uncertainty/integrity fields')
    checks, findings = value['checks'], value['findings']
    if not isinstance(checks, list) or not checks or not isinstance(findings, list):
        raise ValueError('Independent checks/findings missing')
    for check in checks:
        if (not isinstance(check, dict) or set(check) != {'command', 'status', 'exit_code', 'evidence'}
                or not isinstance(check['command'], list) or not check['command']
                or not all(isinstance(c, str) for c in check['command'])
                or check['status'] not in ('pass', 'fail', 'not_run')
                or not (check['exit_code'] is None or type(check['exit_code']) is int)
                or not isinstance(check['evidence'], str)):
            raise ValueError('Invalid independent check evidence')
    for command in protocol.get('audit_required_commands', []):
        if not any(c['command'] == command for c in checks):
            raise ValueError('Required independent verification profile omitted')
    ids = set()
    for finding in findings:
        if (not isinstance(finding, dict) or set(finding) != {'id', 'severity', 'title', 'file', 'line', 'evidence', 'required_action'}
                or not isinstance(finding['id'], str) or not re.fullmatch(r'AUD-[0-9]{3}', finding['id'])
                or finding['id'] in ids or finding['severity'] not in ('critical', 'high', 'normal', 'low')
                or not all(isinstance(finding[k], str) and finding[k] for k in ('title', 'evidence', 'required_action'))
                or not (finding['file'] is None or isinstance(finding['file'], str))
                or not (finding['line'] is None or type(finding['line']) is int and finding['line'] >= 1)):
            raise ValueError('Invalid independent finding')
        ids.add(finding['id'])
    if value['verdict'] == 'PASS' and (findings or value['untested'] or not value['worktree_unchanged']
            or not all(c['status'] == 'pass' and c['exit_code'] == 0 and c['evidence'] for c in checks)):
        raise ValueError('PASS contradicts complete checks/findings/integrity')
    if value['verdict'] == 'FAIL' and not findings:
        raise ValueError('FAIL has no scoped repair findings')
    return value['verdict']




def freeze_source_bytes(site, destination, inventory):
    """Immutable sanitized source copy: no runtime state or native identities."""
    if destination.exists() or destination.is_symlink():
        raise RuntimeError('Refusing source snapshot collision')
    for ancestor in (destination.parent, *destination.parents):
        if ancestor.is_symlink():
            raise RuntimeError('Source snapshot destination symlink forbidden')
    validated = []
    for relative, expected in sorted(inventory.items()):
        path = Path(relative)
        if path.is_absolute() or not path.parts or any(p in ('.', '..') for p in path.parts):
            raise RuntimeError('Unsafe source snapshot path')
        source = site / path
        for depth in range(len(path.parts)+1):
            if (site / Path(*path.parts[:depth])).is_symlink():
                raise RuntimeError('Source snapshot symlink forbidden')
        if digest(source) != expected:
            raise RuntimeError('Source changed before immutable snapshot: ' + relative)
        validated.append((path, source, expected))
    destination.mkdir(parents=True, exist_ok=False)
    try:
        for relative, source, expected in validated:
            target = destination / 'sources' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            # Read/write bytes prevents metadata/private absolute paths leaking.
            target.write_bytes(source.read_bytes())
            if digest(target) != expected or digest(source) != expected:
                raise RuntimeError('Source changed during immutable snapshot: ' + str(relative))
        from phase_collect import source_hashes
        if source_hashes(site) != inventory:
            raise RuntimeError('Source inventory changed during immutable snapshot')
        manifest = {'schema_version': 1, 'sources_sha256': dict(sorted(inventory.items())),
                    'source_file_count': len(inventory), 'source_bytes': sum(source.stat().st_size for _, source, _ in validated)}
        write_json(destination / 'manifest.json', manifest)
        return dict(source_file_count=manifest['source_file_count'], source_bytes=manifest['source_bytes'],
                    manifest_sha256=digest(destination / 'manifest.json'))
    except BaseException:
        # Preserve the failed partial snapshot as evidence; never silently replace it.
        raise

def fixed_gates(protocol, site, directory, round_number, deadline, env):
    out = directory / 'gates' / ('%02d' % round_number)
    out.mkdir(parents=True, exist_ok=False)
    reports = []
    for index, template in enumerate(protocol.get('gate_commands', [])):
        if not isinstance(template, list) or not template or not all(isinstance(v, str) for v in template):
            raise ValueError('Invalid fixed gate argv')
        args = [v.replace('{site}', str(site)).replace('{out}', str(out)).replace('{root}', str(ROOT)) for v in template]
        available = None if deadline is None else deadline-time.monotonic()-protocol['cleanup_reserve_seconds']
        if available is not None and available <= 0:
            raise TimeoutError('Global deadline before fixed gate')
        completed = owned_run(args, cwd=site, env=env,
                              timeout=tool_timeout(protocol, deadline, protocol.get('fixed_gate_cap_seconds', 300)),
                              cleanup_grace=min(1, protocol['cleanup_reserve_seconds'] or 1))
        (out / ('%02d-stdout.json' % index)).write_text(completed.stdout)
        (out / ('%02d-stderr.log' % index)).write_text(completed.stderr)
        report = json.loads(completed.stdout)
        if not isinstance(report, dict) or type(report.get('accepted')) is not bool or type(report.get('tool_incomplete')) is not bool:
            raise ValueError('Fixed gate report acceptance/incompleteness missing')
        reports.append({'command': args, 'exit_code': completed.returncode, 'report': report,
                        'report_path': str(out / ('%02d-stdout.json' % index))})
    return {'accepted': all(r['report']['accepted'] and not r['report']['tool_incomplete'] and r['exit_code'] == 0 for r in reports),
            'tool_incomplete': any(r['report']['tool_incomplete'] for r in reports), 'reports': reports}

def isolated_environment(source):
    env=dict(source)
    for key in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','GEMINI_API_KEY','GOOGLE_API_KEY','GROQ_API_KEY','COHERE_API_KEY','MISTRAL_API_KEY','AI_GATEWAY_API_KEY','DATABASE_URL','DIRECT_URL','AUTH_SECRET','NEXTAUTH_SECRET','BETTER_AUTH_SECRET'):
        env.pop(key,None)
    env['NEXT_TELEMETRY_DISABLED']='1'
    return env


def run(condition):
    from phase_collect import source_hashes
    if condition not in ('single', 'adaptive'):
        raise ValueError('Unknown condition')
    protocol = runtime_protocol(json.loads((ROOT / 'protocol.json').read_text()))
    directory = ROOT / 'runs' / condition
    site = directory / 'site'
    port = protocol['ports'][condition]
    if (directory / 'metadata.json').exists() or (directory / 'phases').exists():
        raise RuntimeError('Refusing already-started condition')
    if not uncapped(protocol) and (protocol['gate_reserve_seconds'] < 2100 or protocol['shared_budget_seconds'] <= protocol['gate_reserve_seconds']):
        raise ValueError('Initial gate reserve must be at least 35 minutes')
    if not uncapped(protocol) and not 1 <= protocol['max_audit_rounds'] <= 4:
        raise ValueError('Audit round ceiling must be between one and four')
    verify_freeze(protocol, site, initial=True)
    env = isolated_environment(os.environ)
    env.update(PREVIEW_NODE=NODE, PREVIEW_PLAYWRIGHT_MODULE=PW, BENCHMARK_NODE=NODE, BENCHMARK_PLAYWRIGHT_IMPORT=PW, PORTAL_PORT=str(port))
    broker = None
    meta = None
    start = None
    failure = None
    log = (directory / 'preview-broker.log').open('w')
    try:
        broker = subprocess.Popen([sys.executable, str(ROOT / 'preview/broker.py'), '--workspace', str(site), '--port', str(port)],
                                  stdout=subprocess.PIPE, stderr=log, text=True, env=env, start_new_session=True)
        ready, _, _ = select.select([broker.stdout], [], [], 30)
        if not ready:
            raise RuntimeError('Browser readiness timeout before timer')
        line = broker.stdout.readline()
        log.write(line); log.flush()
        if not json.loads(line).get('ready') or broker.poll() is not None:
            raise RuntimeError('Browser not ready')
        handshake = subprocess.run([sys.executable, str(site / 'preview_client.py'), '--workspace', str(site), '--ready'], capture_output=True, text=True, timeout=10)
        if handshake.returncode or not json.loads(handshake.stdout).get('ready'):
            raise RuntimeError('Mailbox handshake failed')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', port))
        start = time.monotonic()
        deadline = None if uncapped(protocol) else start + protocol['shared_budget_seconds']
        meta = {'condition': condition, 'start_unix': time.time(), 'state': 'INCOMPLETE',
                'completion_mode': protocol.get('completion_mode', 'capped'),
                'shared_budget_seconds': protocol.get('shared_budget_seconds'), 'phases': [],
                'common_prompt_sha256': protocol['prompt_sha256'],
                'protocol_sha256': digest(ROOT / 'protocol.json'),
                'preview_ready_before_timer': True, 'parent_does_not_start_backend': True,
                'initial_source_sha256': source_hashes(site)}
        write_json(directory / 'metadata.json', meta)
        phase, _ = execute_phase(condition, site, directory, protocol, meta, deadline,
                                 (ROOT / 'APP_PROMPT.txt').read_bytes(), role='builder', number=1, env=env)
        meta['initial_builder_seconds'] = phase['elapsed_seconds']
        verify_freeze(protocol, site)
        if phase['state'] != 'completed':
            raise RuntimeError('Initial builder incomplete')
        meta['initial_ready_source_snapshot'] = freeze_source_bytes(site, directory / 'snapshots' / 'initial', source_hashes(site))
        meta['initial_ready_unix'] = time.time()
        meta['initial_ready_elapsed_seconds'] = time.monotonic()-start
        write_json(directory / 'metadata.json', meta)
        for audit_round in audit_rounds(protocol):
            gates = fixed_gates(protocol, site, directory, audit_round, deadline, env)
            meta.setdefault('fixed_gates', []).append(gates)
            # Owned cleanup is timed and restores assigned port for independent checks.
            meta.setdefault('pre_audit_backend_cleanup', []).append(cleanup_bound_backend(site, port, tuple(protocol.get('backend_command_markers', ['server.py']))))
            packet_args = [str(site / 'quality'), 'audit-packet', '--force', '--criteria',
                           protocol['audit_acceptance_criteria'] if 'audit_acceptance_criteria' in protocol else (site / 'BRIEF.md').read_text()]
            if protocol.get('audit_scope_base'):
                packet_args += ['--base', protocol['audit_scope_base']]
            packet_run = subprocess.run(packet_args, cwd=site, capture_output=True, text=True,
                                        timeout=tool_timeout(protocol, deadline, 60))
            if packet_run.returncode:
                raise RuntimeError('Fresh complete audit packet generation failed: ' + packet_run.stderr[-1000:])
            packet = json.loads(packet_run.stdout)
            packet_path = directory / ('audit-%02d-packet.json' % audit_round)
            write_json(packet_path, packet)
            before = source_hashes(site)
            snapshot_path = directory / ('audit-%02d-source-hashes.json' % audit_round)
            write_json(snapshot_path, before)
            meta.setdefault('source_snapshots', []).append({'round': audit_round, 'sources_sha256': before})
            exact_scope = '\nCanonical scope.base must be exactly: ' + json.dumps(protocol.get('audit_scope_base', packet['base'])) + '\nCanonical scope.acceptance_criteria must be exactly: ' + json.dumps(protocol.get('audit_acceptance_criteria', packet['acceptance_criteria'])) + '\nAll native descendant work must be completed before phase handoff. Complete the full scope independently.'
            audit_prompt = (ROOT / 'AUDIT_PROMPT.txt').read_text() + exact_scope + '\nFresh full-scope audit packet: ' + str(packet_path) + '\nParent source inventory: ' + str(snapshot_path) + '\nIndependent raw fixed-contract reports: ' + json.dumps([r['report_path'] for r in gates['reports']]) + remaining_prompt(deadline)
            audit, audit_dir = execute_phase(condition, site, directory, protocol, meta, deadline,
                                            audit_prompt.encode(), role='auditor', number=len(meta['phases'])+1, env=env)
            verify_freeze(protocol, site)
            if source_hashes(site) != before:
                raise RuntimeError('Auditor changed product sources')
            if audit['state'] != 'completed':
                raise RuntimeError('Independent audit incomplete')
            verdict = json.loads((audit_dir / 'final.txt').read_text())
            gate_protocol = dict(protocol, audit_required_files=packet['changed_files'])
            status = validate_verdict(verdict, site, before, gate_protocol)
            write_json(audit_dir / 'verdict.json', verdict)
            audit['verdict'] = status
            if status == 'PASS' and gates['accepted']:
                meta['state'] = 'PASS'
                meta['accepted_source_sha256'] = before
                meta['accepted_gate_unix'] = time.time()
                break
            if status == 'BLOCKED' or gates['tool_incomplete']:
                meta['state'] = 'BLOCKED'
                break
            if not uncapped(protocol) and audit_round == protocol['max_audit_rounds']:
                meta['state'] = 'FAIL'
                break
            repair_verdict = json.loads(json.dumps(verdict))
            if not gates['accepted']:
                repair_verdict['verdict'] = 'FAIL'
                repair_verdict['findings'].append({'id': 'AUD-999', 'severity': 'high',
                    'title': 'Independent fixed contract gate failed', 'file': None, 'line': None,
                    'evidence': json.dumps([r['report_path'] for r in gates['reports']]),
                    'required_action': 'Repair every failing contract in the referenced raw gate reports; preserve protected fixtures.'})
            repair_path = directory / ('repair-%02d-findings.json' % audit_round)
            write_json(repair_path, repair_verdict)
            repair = ('Continue the original builder session. Repair the complete independent audit findings in '
                      + str(repair_path) + '. Re-run relevant builder verification and generate a new audit packet. '
                      'Do not supply the independent verdict. Keep the common protected corpus unchanged. '
                      + remaining_prompt(deadline)).encode()
            repaired, _ = execute_phase(condition, site, directory, protocol, meta, deadline, repair,
                                        role='builder', number=len(meta['phases'])+1, resume=meta['builder_root'], env=env)
            verify_freeze(protocol, site)
            if repaired['state'] != 'completed':
                raise RuntimeError('Repair builder incomplete')
        # Final confirmation is measured, including protected corpus and accepted source integrity.
        verify_freeze(protocol, site)
        if meta['state'] == 'PASS' and source_hashes(site) != meta['accepted_source_sha256']:
            raise RuntimeError('Accepted sources changed after gate')
        meta['final_source_sha256'] = source_hashes(site)
    except BaseException as exc:
        failure = exc
        if meta is not None:
            meta['state'] = 'INCOMPLETE'
            meta['runner_error'] = type(exc).__name__ + ': ' + str(exc)
    finally:
        cleanup_errors = []
        if meta is not None:
            try:
                final_inventory = source_hashes(site)
                meta['final_source_snapshot'] = freeze_source_bytes(site, directory / 'snapshots' / 'final', final_inventory)
                meta['final_source_sha256'] = final_inventory
                meta['final_snapshot_unix'] = time.time()
                meta['final_snapshot_elapsed_seconds'] = time.monotonic()-start
            except Exception as exc:
                cleanup_errors.append('final source snapshot: ' + str(exc))
            try:
                meta['backend_cleanup'] = cleanup_bound_backend(site, port, tuple(protocol.get('backend_command_markers', ['server.py'])))
            except Exception as exc:
                cleanup_errors.append('backend cleanup: ' + str(exc))
        if broker is not None:
            try:
                terminate_group(broker)
            except Exception as exc:
                cleanup_errors.append('browser cleanup: ' + str(exc))
            if broker.stdout:
                broker.stdout.close()
        log.close()
        if meta is not None:
            meta.update(end_unix=time.time(), elapsed_seconds=time.monotonic()-start, cleanup_errors=cleanup_errors)
            meta['budget_exceeded'] = False if uncapped(protocol) else meta['elapsed_seconds'] > protocol['shared_budget_seconds']
            if cleanup_errors or meta['budget_exceeded']:
                meta['state'] = 'INCOMPLETE'
            write_json(directory / 'metadata.json', meta)
            print(json.dumps({k: meta.get(k) for k in ('condition', 'state', 'initial_builder_seconds', 'elapsed_seconds', 'budget_exceeded', 'cleanup_errors')}), flush=True)
    if failure is not None:
        raise failure
    return meta




def kernel_process_identity(pid):
    """PID reuse protection from native creation time, not second-resolution ps."""
    if sys.platform == 'darwin':
        import ctypes
        class BSDInfo(ctypes.Structure):
            _fields_ = [('head', ctypes.c_uint32 * 12), ('comm', ctypes.c_char * 16),
                        ('name', ctypes.c_char * 32), ('tail', ctypes.c_uint32 * 6),
                        ('start_sec', ctypes.c_uint64), ('start_usec', ctypes.c_uint64)]
        info = BSDInfo()
        library = ctypes.CDLL('/usr/lib/libproc.dylib')
        if library.proc_pidinfo(pid, 3, 0, ctypes.byref(info), ctypes.sizeof(info)) != ctypes.sizeof(info):
            return None
        if info.head[1] == 5:  # SZOMB: no executable resources remain.
            return None
        return (info.start_sec, info.start_usec)
    if sys.platform.startswith('linux'):
        try:
            fields = Path('/proc/' + str(pid) + '/stat').read_text().rsplit(')', 1)[1].split()
            if fields[0] == 'Z':
                return None
            return (int(fields[19]),)
        except (OSError, ValueError, IndexError):
            return None
    raise RuntimeError('Exact process creation identity unsupported on this platform')

def process_inventory():
    """Kernel process identity/ancestry, kept in memory without publishing commands."""
    result = subprocess.run(['ps', '-axo', 'pid=,ppid=,pgid=,lstart=,command='],
                            capture_output=True, text=True, timeout=3)
    if result.returncode:
        raise RuntimeError('Owned process inventory unavailable')
    rows = {}
    for line in result.stdout.splitlines():
        fields = line.split(None, 8)
        if len(fields) != 9 or not all(f.isdigit() for f in fields[:3]):
            continue
        pid, parent, group = map(int, fields[:3])
        identity = kernel_process_identity(pid)
        if identity is not None:
            rows[pid] = {'parent': parent, 'group': group, 'identity': identity}
    return rows


class OwnedHierarchy:
    """Track only proven descendants, preserving ownership after setsid/reparenting."""
    def __init__(self, process, inventory, ledgers=()):
        import threading
        self.process = process
        self.root = process.pid
        self.owned = {}
        self.groups = {}
        self.errors = []
        self.ledgers = tuple(ledgers)
        self.stop_event = threading.Event()
        self.observe(inventory)
        if self.root not in self.owned:
            # A fast successful child can already be reaped by communicate; the
            # caller must start tracking immediately after Popen, before waiting.
            raise RuntimeError('Owned hierarchy root identity unavailable')
        self.worker = threading.Thread(target=self.monitor, daemon=True)
        self.worker.start()

    def observe(self, inventory):
        if not self.owned and self.root in inventory:
            self.owned[self.root] = inventory[self.root]['identity']
            self.groups[self.root] = inventory[self.root]['identity']
        live = {pid for pid, identity in self.owned.items()
                if pid in inventory and inventory[pid]['identity'] == identity}
        while True:
            children = {pid for pid, row in inventory.items() if row['parent'] in live}
            new = children - live
            if not new:
                break
            for pid in new:
                self.owned[pid] = inventory[pid]['identity']
                if inventory[pid]['group'] == pid:
                    self.groups[pid] = inventory[pid]['identity']
            live |= new

    def registrations(self):
        pending = []
        for ledger in self.ledgers:
            for line in Path(ledger).read_text().splitlines():
                if line:
                    pending.append(json.loads(line))
        while pending:
            advanced = False
            for row in pending[:]:
                if self.owned.get(row['parent']) == tuple(row['parent_identity']):
                    identity = tuple(row['identity'])
                    if row['pid'] in self.owned and self.owned[row['pid']] != identity:
                        raise RuntimeError('Gate child PID creation identity collision')
                    self.owned[row['pid']] = identity
                    if row.get('group') == row['pid']:
                        self.groups[row['pid']] = identity
                    pending.remove(row); advanced = True
            if not advanced:
                # Other inherited outer-ledger siblings are not owned by an
                # inner wrapper and are ignored there. The outer owner consumes them.
                break

    def monitor(self):
        while not self.stop_event.wait(.03):
            try:
                self.observe(process_inventory())
            except Exception as exc:
                self.errors.append(type(exc).__name__ + ': process ancestry observation failed')
                return

    def cleanup(self, grace=1):
        self.stop_event.set()
        self.worker.join(timeout=4)
        if self.worker.is_alive():
            raise RuntimeError('Owned hierarchy monitor did not stop')
        self.registrations()
        self.observe(process_inventory())
        # Graceful wrapper termination permits its nested ownership cleanup.
        for sig in (signal.SIGTERM, signal.SIGKILL):
            self.registrations()
            inventory = process_inventory()
            for group, birth in self.groups.items():
                members = {pid: row for pid, row in inventory.items() if row['group'] == group}
                if not members:
                    continue
                if group in inventory and inventory[group]['identity'] != birth:
                    raise RuntimeError('Owned process group ID was reused')
                if not any(self.owned.get(pid) == row['identity'] for pid, row in members.items()):
                    raise RuntimeError('Owned group has live unregistered members with uncertain ancestry')
                try:
                    os.killpg(group, sig)
                except ProcessLookupError:
                    pass
            for pid, identity in list(self.owned.items()):
                if pid not in inventory or inventory[pid]['identity'] != identity or kernel_process_identity(pid) != identity:
                    continue  # Revalidate exact kernel creation identity immediately before signaling.
                try:
                    os.kill(pid, sig)
                except ProcessLookupError:
                    pass
            if sig == signal.SIGTERM:
                until = time.monotonic() + grace
                while time.monotonic() < until:
                    self.process.poll()
                    inventory = process_inventory()
                    # Continue tracking while parents gracefully close resources.
                    self.registrations()
                    self.observe(inventory)
                    if not any(pid in inventory and inventory[pid]['identity'] == identity
                               for pid, identity in self.owned.items()):
                        break
                    time.sleep(.03)
        self.process.wait(timeout=2)
        until = time.monotonic() + 2
        while any(kernel_process_identity(pid) == identity for pid, identity in self.owned.items()):
            if time.monotonic() >= until:
                raise RuntimeError('Owned detached descendants remain live after cleanup')
            time.sleep(.02)
        if self.errors:
            raise RuntimeError('; '.join(self.errors))
        inventory = process_inventory()
        if any(row['group'] in self.groups for row in inventory.values()):
            raise RuntimeError('Registered owned process group still has live resources')
        return {'owned_process_count': len(self.owned), 'registered_process_group_count': len(self.groups),
                'scope': 'Registered Python/Node/Playwright gate launches and proven descendant groups'}


def owned_run(args, *, timeout, cwd, env, cleanup_grace=1):
    """communicate timeout plus explicit descendant cleanup, including detached nodes."""
    import tempfile
    process_inventory()
    temporary = tempfile.TemporaryDirectory(prefix='owned-gate-ledger-')
    ledger = Path(temporary.name) / 'children.jsonl'
    ledger.write_text('')
    child_env = env.copy()
    inherited_ledgers = json.loads(child_env.get('CODEX_GATE_LEDGERS', '[]'))
    child_env['CODEX_GATE_LEDGERS'] = json.dumps(inherited_ledgers + [str(ledger)])
    support = ROOT / 'gate_support'
    child_env['PYTHONPATH'] = str(support) + os.pathsep + str(ROOT) + (os.pathsep + child_env['PYTHONPATH'] if child_env.get('PYTHONPATH') else '')
    child_env['CODEX_GATE_PYTHON'] = sys.executable
    # NODE_OPTIONS is an option string, not shell code. Quote paths according
    # to Node's double-quoted option parser, preserving existing options.
    preload = str(support / 'preload.cjs').replace('\\', '\\\\').replace('"', '\\"')
    child_env['NODE_OPTIONS'] = (child_env.get('NODE_OPTIONS', '') + ' --require="' + preload + '"').strip()
    read_fd, write_fd = os.pipe()
    # Keep the exact root alive until ancestry tracking is active. The wrapper
    # then execs the requested argv, preserving kernel PID creation identity.
    barrier = ('import json,os,sys; fd=int(sys.argv[1]); argv=json.loads(sys.argv[2]); '
               'ready=os.read(fd,1); os.close(fd); '
               'os._exit(125) if ready!=b"1" else os.execvpe(argv[0],argv,os.environ)')
    process = None
    hierarchy = None
    try:
        process = subprocess.Popen([sys.executable, '-c', barrier, str(read_fd), json.dumps(args)],
                                   cwd=cwd, env=child_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, start_new_session=True, pass_fds=(read_fd,))
        os.close(read_fd); read_fd = None
        hierarchy = OwnedHierarchy(process, process_inventory(), inherited_ledgers + [str(ledger)])
        os.write(write_fd, b'1'); os.close(write_fd); write_fd = None
        stdout, stderr = process.communicate(timeout=timeout)
        return subprocess.CompletedProcess(args, process.returncode, stdout, stderr)
    finally:
        if read_fd is not None:
            os.close(read_fd)
        if write_fd is not None:
            os.close(write_fd)
        if process is not None:
            try:
                if hierarchy is not None:
                    hierarchy.cleanup(grace=cleanup_grace)
                else:
                    terminate_group(process, grace=cleanup_grace)
            finally:
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()
        temporary.cleanup()


if __name__ == '__main__':
    run(sys.argv[1])

"""Gate-only Python resource registration; never added to native builder env."""
import os
import subprocess

if os.environ.get('CODEX_GATE_LEDGERS'):
    try:
        from gate_registration import register
    except BaseException:
        os._exit(124)  # Python otherwise suppresses sitecustomize initialization errors.
    original = subprocess.Popen.__init__

    def registered_init(self, *args, **kwargs):
        original(self, *args, **kwargs)
        # ps is the short-lived read-only ownership observer itself. All other
        # Python subprocess children register before Popen returns to the caller.
        argv = kwargs.get('args', args[0] if args else None)
        executable = argv[0] if isinstance(argv, (tuple, list)) and argv else argv
        if executable == 'ps':
            return
        try:
            register(self.pid, os.getpid())
        except BaseException:
            self.terminate()
            self.wait(timeout=2)
            raise
    subprocess.Popen.__init__ = registered_init

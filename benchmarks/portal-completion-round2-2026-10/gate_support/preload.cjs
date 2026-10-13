// Scoped trusted gate preload. Register Node/Playwright children synchronously
// before spawn returns, including Chromium's detached POSIX process group.
const cp = require('node:child_process');
const path = require('node:path');
if (process.env.CODEX_GATE_LEDGERS) {
  const original = cp.spawn;
  cp.spawn = function(...args) {
    const child = original.apply(this, args);
    if (Number.isInteger(child.pid)) {
      try {
        cp.execFileSync(process.env.CODEX_GATE_PYTHON,
          [path.join(__dirname, 'gate_registration.py'), String(child.pid), String(process.pid)],
          {env:process.env, stdio:['ignore','ignore','pipe'], timeout:5000});
      } catch (error) {
        child.kill('SIGTERM');
        throw Error('Synchronous gate child registration failed: ' + error.message);
      }
    }
    return child;
  };
  require('node:module').syncBuiltinESMExports();
}

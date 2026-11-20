import { fork } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const [mode, library] = process.argv.slice(2);
if (mode === '--loaded-child') {
  const loaded = { exports: {} };
  process.dlopen(loaded, library);
  process.send({ ready: true, modulePid: process.pid });
  process.on('message', message => { if (message === 'stop') process.disconnect(); });
} else {
  // host -> browser-root -> GPU-like grandchild. Only the last process loads
  // the fixture image; forwarding a path in argv is not module evidence.
  const child = fork(fileURLToPath(import.meta.url),
    [mode === '--host' ? '--browser-root' : '--loaded-child', library],
    { stdio: ['ignore', 'ignore', 'inherit', 'ipc'] });
  child.on('message', message => process.send({ ...message,
    ...(mode === '--browser-root' ? { browserPid: process.pid } : {}) }));
  process.on('message', message => child.send(message));
  child.on('exit', code => process.exit(code ?? 1));
  process.on('disconnect', () => child.kill('SIGKILL'));
}

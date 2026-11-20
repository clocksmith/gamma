import { fork } from 'node:child_process';
import { fileURLToPath } from 'node:url';

// A real owned descendant, with and without a listener, supplies an independent
// negative control for OS socket inspection. Neither process is a browser mock.
if (process.argv[2] === '--listener') {
  const { createServer } = await import('node:http');
  const server = createServer((_request, response) => response.end('ok'));
  server.listen(0, '127.0.0.1', () => process.send({ ready: true, pid: process.pid }));
  process.on('message', (message) => {
    if (message === 'close-listener') server.close(() => process.send({ listenerClosed: true }));
    if (message === 'stop') {
      server.close();
      process.disconnect();
    }
  });
} else {
  const child = fork(fileURLToPath(import.meta.url), ['--listener', process.argv[2]], { stdio: ['ignore', 'ignore', 'inherit', 'ipc'] });
  child.on('message', (message) => process.send(message));
  process.on('message', (message) => child.send(message));
  child.on('exit', (code) => process.exit(code ?? 1));
  process.on('disconnect', () => child.kill('SIGKILL'));
}

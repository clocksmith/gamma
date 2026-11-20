// Fawn workspace qualification — parent side of service-host.js.
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { fileURLToPath } from 'node:url';

const HOST_PATH = fileURLToPath(new URL('./service-host.js', import.meta.url));

class HostError extends Error {
  constructor(error) {
    super(error.message);
    this.code = error.code;
  }
}

/**
 * Start a service host and resolve once it has restored authority (or failed to).
 */
function startHost(options, hostPath = HOST_PATH) {
  const child = spawn(process.execPath, [hostPath, JSON.stringify(options)], { stdio: ['pipe', 'pipe', 'inherit'] });
  const pending = new Map();
  let nextId = 1;
  let terminationRequest = null;
  // close follows stdout drain: a self-kill receipt must arrive before the
  // parent records/rejects the final OS exit.
  const exited = new Promise((resolve) => child.on('close', (code, signal) => resolve({ code, signal })));
  const ready = new Promise((resolve, reject) => {
    createInterface({ input: child.stdout }).on('line', (line) => {
      const message = JSON.parse(line);
      if (message.event === 'ready') resolve();
      else if (message.event === 'open-failed') reject(new HostError(message.error));
      else if (message.event === 'termination-requested') {
        if (message.pid !== child.pid || message.signal !== 'SIGKILL') throw new Error('invalid host termination receipt');
        terminationRequest = { source: 'host-hook', pid: message.pid, signal: message.signal };
      }
      else {
        const waiter = pending.get(message.id);
        pending.delete(message.id);
        if (message.ok) waiter.resolve(message.result);
        else waiter.reject(new HostError(message.error));
      }
    });
    exited.then(({ code, signal }) => {
      const error = new Error(`service host exited (${signal ?? code})`);
      error.exit = { code, signal };
      for (const waiter of pending.values()) waiter.reject(error);
      pending.clear();
      reject(error);
    });
  });
  const send = (op, args) => new Promise((resolve, reject) => {
    const id = nextId++;
    pending.set(id, { resolve, reject });
    child.stdin.write(`${JSON.stringify({ id, op, args })}\n`);
  });
  return ready.then(() => ({
    request: send,
    call: (method, args) => send('call', { method, args }),
    submitAndWait: (args) => send('submitAndWait', args),
    submit: (args) => send('submit', args),
    awaitAction: (actionId) => send('awaitAction', { actionId }),
    queueBehindEffect: (args) => send('queueBehindEffect', args),
    awaitAdmission: (actionId) => send('awaitAdmission', { actionId }),
    workflow: (name, owner, task, fault = null, sessionOptions = {}) => send('workflow', {
      name,
      owner,
      task,
      fault,
      sessionOptions,
    }),
    raceWorkflow: (args) => send('raceWorkflow', args),
    surface: (owner) => send('surface', { owner }),
    close: async () => {
      await send('close', {});
      return exited;
    },
    kill: () => {
      if (!child.kill('SIGKILL')) throw new Error(`failed to request forced termination of host ${child.pid}`);
      terminationRequest = { source: 'controller', pid: child.pid, signal: 'SIGKILL' };
      return exited;
    },
    terminationRequest: () => terminationRequest,
    exited,
    pid: child.pid,
  }));
}

export { startHost };

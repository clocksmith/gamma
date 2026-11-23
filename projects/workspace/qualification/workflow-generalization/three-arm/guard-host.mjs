// Runs inside the guard sandbox container (see guard-sandbox.mjs). It loads the
// model-written guard, hands it one route and a `get` function, and reports the
// guard's answer. The container has no network: `get` is a message to the runner
// outside, which performs the read through the decision surface.
import readline from 'node:readline';

const lines = readline.createInterface({ input: process.stdin, crlfDelay: Infinity })[Symbol.asyncIterator]();
const first = JSON.parse((await lines.next()).value);
const { nonce, route } = first;
const say = message => process.stdout.write(`${nonce} ${JSON.stringify(message)}\n`);
const waiting = new Map();
let nextId = 1;

(async () => {
  for await (const line of { [Symbol.asyncIterator]: () => lines }) {
    if (!line.startsWith(`${nonce} `)) continue;
    const message = JSON.parse(line.slice(nonce.length + 1));
    if (message.type === 'got' && waiting.has(message.id)) {
      waiting.get(message.id)(message.result);
      waiting.delete(message.id);
    }
  }
})();

const get = path => new Promise(resolveGet => {
  const id = nextId++;
  waiting.set(id, resolveGet);
  say({ type: 'get', id, path });
});

try {
  const guard = await import('/guard/guard.mjs');
  if (typeof guard.decide !== 'function') throw Error('guard.mjs must export an async function decide');
  const answer = await guard.decide({ ...route, get });
  const decision = answer?.decision === 'write' ? 'write' : 'stop';
  say({ type: 'decision', decision, reason: typeof answer?.reason === 'string' ? answer.reason.slice(0, 300) : null });
} catch (error) {
  say({ type: 'error', message: String(error?.stack ?? error).slice(0, 1200) });
}
process.exit(0);

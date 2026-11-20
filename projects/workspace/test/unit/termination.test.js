import assert from 'node:assert/strict';
import { abruptExitMatches, terminationMatches } from '../../qualification/termination.js';

for (const platform of ['linux', 'darwin']) {
  assert.equal(abruptExitMatches({ code: null, signal: 'SIGKILL' }, platform), true);
  assert.equal(abruptExitMatches({ code: null, signal: 'SIGTERM' }, platform), false);
  assert.equal(abruptExitMatches({ code: 0, signal: null }, platform), false);
  assert.equal(abruptExitMatches({ code: 1, signal: null }, platform), false);
}
assert.equal(abruptExitMatches({ code: 1, signal: null }, 'win32', 'host-hook'), true);
assert.equal(abruptExitMatches({ code: null, signal: 'SIGKILL' }, 'win32', 'controller'), true);
for (const code of [0, 2, null]) assert.equal(abruptExitMatches({ code, signal: null }, 'win32', 'host-hook'), false);
assert.equal(abruptExitMatches({ code: null, signal: 'SIGKILL' }, 'win32', 'host-hook'), false);
assert.equal(abruptExitMatches({ code: 1, signal: null }, 'win32', 'controller'), false);
assert.equal(abruptExitMatches({ code: 1, signal: null }, 'win32'), false);
assert.equal(abruptExitMatches({ code: 1, signal: null }, 'unknown'), false);
const request = { pid: 42, signal: 'SIGKILL', source: 'host-hook' };
const evidence = { requestedSignal: 'SIGKILL', abrupt: true, hostPid: 42, request, rawExit: { code: 1, signal: null } };
assert.equal(terminationMatches(evidence, 'win32'), true);
assert.equal(terminationMatches({ ...evidence, request: null }, 'win32'), false);
assert.equal(terminationMatches({ ...evidence, hostPid: 43 }, 'win32'), false);
assert.equal(terminationMatches({ ...evidence, request: { ...request, source: 'unobserved' } }, 'win32'), false);
console.log('ok: raw forced-termination evidence and ordinary-exit rejection');

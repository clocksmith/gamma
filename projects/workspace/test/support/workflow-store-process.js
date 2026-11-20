// Separate-process storage fixture. Controlled planning proves persistence, not model quality.
import fs from 'node:fs';
import { syncBuiltinESMExports } from 'node:module';
import { join } from 'node:path';
import { WorkflowSync } from '../../src/client/workflow-sync.js';
import { WorkflowStore } from '../../src/client/workflow-store.js';
import { InvestigationStore } from '../../src/client/investigation.js';
import { sha256Hex } from '../../src/journal.js';

process.once('message', async message => {
  const { directory, mode = 'learn', label = 'Name', accountScope = 'account-a', ownerScope = 'person-a' } = message;
  const store = new InvestigationStore(join(directory, `run-${process.pid}`));
  const persistent = new WorkflowStore({ directory: join(directory, 'cache'), ownerScope,
    limits: { maxNodes: 32, maxEdges: 32, maxSteps: 8 }, maxBytes: message.maxBytes ?? 100000,
    attemptMaxBytes: message.attemptMaxBytes ?? 100000,
    lockWaitMs: 200, lockRetryMs: 5, sync: message.sync ? new WorkflowSync({ ...message.sync, ownerScope }) : null });
  let value = '', version = 0, checks = 0;
  const calls = [];
  const service = { outstanding: async () => [],
    observe: async () => ({ url: 'https://fixture.invalid/application', text: 'Review', isTruncated: false,
      observationVersion: ++version, elements: [{ handle: 'name', selector: '#name', digest: 'live',
        label, role: 'textbox', tag: 'input', inputType: 'text', value }] }),
    submitAction: async request => {
      calls.push(request);
      if (!message.unknown) value = request.params.value;
      return { result: Promise.resolve({ outcome: message.unknown ? 'unknown' : 'completed', isUncertain: !!message.unknown }) };
    },
  };
  const projectId = `run-${process.pid}`;
  store.create({ id: projectId, goal: 'Review fixture' });
  try {
    const result = await persistent.run({ mode, accountScope, template: 'test-form', service, owner: {},
      pageId: 'main', intent: 'form', inputs: { name: message.value ?? 'NEW_PRIVATE_NAME', ssn: 'PRIVATE_SENSITIVE_SLOT' },
      verificationId: 'synthetic-name-review-v1', taskSourceHashes: { fixture: sha256Hex(fs.readFileSync(new URL(import.meta.url))) },
      task: 'Fill name and review', config: { maxTurns: 4, maxInputBytes: 20000 }, store, projectId,
      signal: new AbortController().signal,
      verifyAccount: async () => ++checks >= (message.switchAccountAt ?? Infinity) ? 'account-other' : accountScope,
      disclosurePolicy: { origin: 'https://fixture.invalid', intermediateClicks: [],
        fields: [{ kind: 'fill', slot: 'name', locator: ['textbox', message.denied ? 'Other field' : label, 'input', 'text'] }] },
      planner: { identity: { model: 'controlled' }, next: async () => value
        ? { tool: 'finish', input: { summary: 'Review' } }
        : { tool: 'act', input: { kind: 'fill', handle: 'name', slot: 'name' } } },
      verifyReview: async () => {
        if (message.barrier) {
          process.send({ phase: 'verified' });
          await new Promise(resolve => process.once('message', resolve));
        }
        if (message.pauseWrite) {
          const rename = fs.renameSync;
          fs.renameSync = (from, to) => {
            if (to === persistent.path) {
              fs.writeFileSync(join(directory, 'writer-paused'), 'before-rename');
              process.kill(process.pid, 'SIGSTOP');
            }
            return rename(from, to);
          };
          syncBuiltinESMExports();
        }
        return { completed: !!value && !message.rejectReview };
      },
    });
    process.send({ result, value, calls: calls.length });
  } catch (error) { process.send({ error: error.message, code: error.code }); process.exitCode = 1; }
  finally { store.close(); process.disconnect(); }
});

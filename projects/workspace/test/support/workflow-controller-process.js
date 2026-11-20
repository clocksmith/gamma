// Real Chromium child process. The trusted task oracle is specific to the synthetic fixture.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { WorkspaceService } from '../../src/service.js';
import { testBrowserSelection } from './browser-selection.js';
import { inspectBrowserProcesses } from '../../qualification/identity.js';
import { createPlaywrightAdapter } from '../../src/adapters/playwright-adapter.js';
import { WorkflowSync } from '../../src/client/workflow-sync.js';
import { WorkflowStore } from '../../src/client/workflow-store.js';
import { WorkspaceController } from '../../src/client/controller.js';
import { sha256Hex } from '../../src/journal.js';

process.once('message', async ({ root, url, mode, accountScope, inputs, sync, scoped = false, changed = false }) => {
  let service, controller, adapter;
  try {
    const config = JSON.parse(readFileSync(new URL('../../config/fawn-workspace-client.json', import.meta.url)));
    const selected = testBrowserSelection(root);
    service = await WorkspaceService.open({ stateDir: join(root, `service-${process.pid}`),
      config: selected.config,
      createAdapter: options => adapter = createPlaywrightAdapter(options) });
    const origin = new URL(url).origin;
    const fields = [
      { slot: 'fullName', kind: 'fill', locator: ['textbox', 'Full name', 'input', 'text'] },
      { slot: 'email', kind: 'fill', locator: ['textbox', 'Email address', 'input', 'email'] },
      { slot: 'location', kind: 'fill', locator: ['textbox', 'Current city', 'input', 'text'] },
      { slot: 'workMode', kind: 'select', locator: ['combobox', 'Work arrangement', 'select', ''] },
      ...(scoped ? [{ slot: 'phone', kind: 'fill', locator: ['textbox', 'Phone number', 'input', 'tel'] }] : []),
    ];
    const planner = { identity: { model: 'controlled-browser' }, next: async context => {
      for (const field of fields) {
        const element = context.observation.elements.find(value => value.label === field.locator[1]);
        if (element && element.value !== context.inputs[field.slot]) {
          return { tool: 'act', input: { kind: field.kind, handle: element.handle, slot: field.slot } };
        }
      }
      const button = context.observation.elements.find(value => value.tag === 'button'
        && ['Continue', 'Review application'].includes(value.label));
      return button ? { tool: 'act', input: { kind: 'click', handle: button.handle } }
        : { tool: 'finish', input: { summary: 'Review reached' } };
    } };
    const workflowStore = new WorkflowStore({ directory: join(root, 'shared-cache'), ownerScope: 'synthetic-person',
      limits: { maxNodes: 64, maxEdges: 64, maxSteps: 12 }, maxBytes: 200000, lockWaitMs: 1000, lockRetryMs: 10, sync: sync ? new WorkflowSync({ ...sync, ownerScope: 'synthetic-person' }) : null });
    let rendered;
    const template = 'synthetic-application-v1';
    controller = new WorkspaceController({ service, stateDir: join(root, `client-${process.pid}`), config,
      workflowStore, workflowTasks: new Map([[template, {
        accountScope, task: 'Complete requested fields and stop at review', planner,
        fieldGroups: scoped ? [{ id: 'contact', steps: [
          ...fields.slice(0, 2).map(({ slot, kind, locator }) => ({ slot, kind, locators: [locator] })),
          { kind: 'click', locators: [['button', 'Continue', 'button', '']] },
        ] }, { id: 'questions', steps: [
          ...fields.slice(2, 4).map(({ slot, kind, locator }) => ({ slot, kind, locators: [locator] })),
          { kind: 'click', locators: [['button', 'Review application', 'button', '']] },
        ] }] : null,
        disclosurePolicy: { origin, fields,
          intermediateClicks: [['button', 'Continue', 'button', ''], ['button', 'Review application', 'button', '']] },
        verificationId: 'synthetic-application-review-v1',
        taskSourceHashes: { controllerFixture: sha256Hex(readFileSync(new URL(import.meta.url))),
          applicationFixture: sha256Hex(readFileSync(new URL('./application-fixture.js', import.meta.url))) },
        verifyAccount: ({ owner, pageId }) => adapter._page(owner.workspaceId, pageId)
          .evaluate(() => document.documentElement.dataset.account),
        verifyReview: async ({ owner, pageId, inputs: profile }) => {
          rendered = await adapter._page(owner.workspaceId, pageId).evaluate(() => ({
            stage: document.querySelector('main').dataset.stage,
            fields: Object.fromEntries([...document.querySelectorAll('dl > div')].map(row =>
              [row.querySelector('dt').textContent, row.querySelector('dd').textContent])),
          }));
          const expected = fields.filter(field => field.slot !== 'phone' || changed);
          return { completed: rendered.stage === 'review' && Object.keys(rendered.fields).length === expected.length
            && expected.every(field => rendered.fields[field.locator[1]] === profile[field.slot]) };
        },
      }]]) });
    const { id } = await controller.create({ goal: 'Personal workflow fixture' });
    await controller.navigate(id, { pageId: 'main', url });
    const { done } = await controller.runPersonalWorkflow(id, { template, mode, inputs, pageId: 'main' });
    const result = await done;
    const state = await service.inspect(controller.admin(id));
    process.send({ result, rendered, run: controller.store.get(id).run, owner: state.ownerId,
      browser: selected.config.browser,
      inspection: selected.config.browser.channel === 'fawn'
        ? inspectBrowserProcesses(process.pid, join(root, `service-${process.pid}`, 'profiles')) : null,
      activeAgentGrants: state.grants.filter(grant => grant.ownerId === 'agent' && !grant.revokedAt),
      submitted: state.actions.some(action => action.kind === 'submit') });
  } catch (error) { process.send({ error: error.stack }); process.exitCode = 1; }
  finally { if (controller) await controller.close(); if (service) await service.close(); process.disconnect(); }
});

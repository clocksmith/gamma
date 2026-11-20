// Competent direct-browser control: same fresh facts and value-settling duration,
// conventional Playwright effects and a durable progress file, without Fawn dispatch.
import { randomUUID } from 'node:crypto';
import { buildSnapshot, queryPage, snapshotArgs } from '../../src/adapters/page-query.js';

export function scriptDriver({ page, config, progress, operationId, fault, purchaseAllowed }) {
  const saved = progress.read({ actions: {} });
  const trace = [];
  let observation;
  return {
    identity: { workspaceId: operationId }, trace,
    async observe() { observation = buildSnapshot(await page.evaluate(queryPage, snapshotArgs(config)), 1); return observation; },
    outstanding: async () => Object.values(saved.actions).filter(action => action.isUncertain),
    async act(seen, spec) {
      const actionId = spec.actionId ?? randomUUID();
      if (spec.effect?.external && !purchaseAllowed()) throw Error('Purchase permission revoked');
      if (Object.hasOwn(saved.actions, actionId)) throw Error('An attempt cannot be submitted twice');
      if (spec.effect?.external && Object.values(saved.actions).some(action => action.purchase)) throw Error('Purchase already attempted');
      saved.actions[actionId] = { actionId, kind: spec.kind, purchase: !!spec.effect?.external, outcome: null, isUncertain: true };
      progress.write(saved);
      let outcome = 'completed';
      try {
        if (spec.kind === 'navigate') await page.goto(spec.target.url);
        else {
          const element = seen.elements.find(value => value.handle === spec.target.handle);
          if (!element) throw Error('No current control');
          const target = page.locator(element.selector);
          if (await target.count() !== 1) throw Error('Ambiguous target');
          if (spec.kind === 'fill' || spec.kind === 'select') {
            if (spec.kind === 'fill') await target.fill(spec.params.value);
            else await target.selectOption({ label: spec.params.value });
            await page.waitForTimeout(config.dispatch.valueSettleMs);
            if (await target.inputValue() !== spec.params.value) throw Error('Value did not settle');
          } else await target.click();
        }
        if (spec.effect?.external && ['lost-acknowledgment', 'browser-restart', 'missing-receipt'].includes(fault)) throw Error('Injected lost acknowledgment');
      } catch { outcome = 'unknown'; }
      const result = { actionId, kind: spec.kind, purchase: !!spec.effect?.external, outcome, isUncertain: outcome === 'unknown' };
      trace.push({ kind: spec.kind, label: seen.elements.find(value => value.handle === spec.target?.handle)?.label ?? null,
        value: spec.params?.value ?? null, purchase: !!spec.effect?.external, outcome });
      saved.actions[actionId] = result; progress.write(saved);
      return result;
    },
    action: async actionId => saved.actions[actionId],
    async reconcile({ actionId, effectPresentWhen }) {
      const action = saved.actions[actionId];
      if (!action?.isUncertain || !effectPresentWhen.length) throw Error('No uncertain attempt or receipt condition');
      for (const condition of effectPresentWhen) {
        const target = page.locator(condition.selector);
        if (condition.kind !== 'element-text-includes' || await target.count() !== 1
          || !(await target.innerText()).includes(condition.value)) return action;
      }
      const resolved = { ...action, isUncertain: false, reconciliation: 'effect-present' };
      saved.actions[actionId] = resolved; progress.write(saved); return resolved;
    },
  };
}

// A declared authored decision rule for harness development, not a language model.
export const controlledFieldPlanner = {
  identity: { kind: 'authored-field-rules', model: null },
  async next({ observation, inputs, bindings }) {
    for (const field of bindings) {
      const matches = observation.elements.filter(el => field.labels.includes(el.label));
      if (matches.length !== 1) throw Error('Ambiguous or missing field meaning');
      if (matches[0].value !== inputs[field.slot]) return { handle: matches[0].handle, slot: field.slot };
    }
    throw Error('No outstanding field');
  },
};

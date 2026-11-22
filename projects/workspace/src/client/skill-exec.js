// A recovery-capable executable skill: the baseline that trace-graph replay is compared with.
// It is inspired by executable-skill systems such as WebXSkill and does not reproduce any of them.
//
// A skill is the ordered list of actions a verified teaching run took, with input slots in place of
// values. It keeps no page-state graph. `skillPlanner` stands where a planner stands in runWorkflow,
// so every action it proposes passes the same observation scope, session checks, step
// authorization, prerequisite check, service dispatch checks and journal as any planner action. It
// only decides who proposes the next action: the script, at no model cost, or the real planner.
//
// The script hands the turn to the planner when
//   - the next step's target is missing or not unique on the page, or its input slot is absent;
//   - the next step is a click and the page holds an empty writable control that was not there when
//     the click was taught (leaving could skip a new question);
//   - the script is finished but the planner had to act during the run (the planner decides when
//     the result is ready).
// A fill whose value is already on the page, or whose slot the planner already supplied, is skipped.
// A step refused as stale before dispatch is proposed again on the fresh page.
import { structuralLocator } from '../adapters/page-query.js';
import { canonicalJson } from '../journal.js';

const WRITABLE_TAGS = new Set(['input', 'select', 'textarea']);
const WRITABLE_ROLES = new Set(['textbox', 'searchbox', 'combobox', 'listbox', 'spinbutton', 'checkbox', 'radio', 'switch', 'slider']);
const keyOf = element => canonicalJson(structuralLocator(element));
const isWritable = element => WRITABLE_TAGS.has(element.tag) || WRITABLE_ROLES.has(element.role);
const isEmpty = element => element.value === '' || element.value === null || element.value === undefined;

/** Wrap a teaching run's planner. After the run verifies, `skill()` is its script. */
export function skillRecorder(planner) {
  const steps = [];
  let pending = null;
  const settle = context => {
    if (pending && context?.lastResult?.status === 'completed' && context.lastResult.kind === pending.kind) steps.push(pending);
    pending = null;
  };
  return {
    planner: {
      identity: planner.identity,
      next: async (context, ...rest) => {
        settle(context);
        const decision = await planner.next(context, ...rest);
        if (decision?.tool === 'act') {
          const element = context.observation.elements.find(candidate => candidate.handle === decision.input.handle);
          if (element) {
            pending = { kind: decision.input.kind, locator: structuralLocator(element),
              ...(decision.input.slot === undefined ? {} : { slot: decision.input.slot }),
              // The writable controls on the page when this step was taught.
              page: [...new Set(context.observation.elements.filter(isWritable).map(keyOf))].sort() };
          }
        }
        return decision;
      },
    },
    skill: () => structuredClone({ version: 1, steps }),
  };
}

export function validateSkill(skill) {
  if (skill?.version !== 1 || !Array.isArray(skill.steps) || !skill.steps.length) throw Error('Invalid skill');
  for (const step of skill.steps) {
    if (!['fill', 'select', 'click'].includes(step.kind) || !Array.isArray(step.locator) || step.locator.length !== 4
      || step.locator.some(part => typeof part !== 'string') || !Array.isArray(step.page)
      || (step.kind === 'click' ? step.slot !== undefined : typeof step.slot !== 'string')) throw Error('Invalid skill step');
  }
  return skill;
}

/** A planner that runs `skill` and hands a turn to `planner` under the conditions listed above. */
export function skillPlanner({ skill, planner }) {
  const steps = validateSkill(structuredClone(skill)).steps.map(step => ({ ...step, key: canonicalJson(step.locator), taught: new Set(step.page) }));
  const suppliedByPlanner = new Set();
  const stats = { scriptSteps: 0, handBacks: 0, skippedSteps: 0, retries: 0, reasons: {} };
  let at = 0, pending = null, handed = false;

  const handBack = async (reason, context, rest) => {
    stats.handBacks += 1;
    stats.reasons[reason] = (stats.reasons[reason] ?? 0) + 1;
    handed = true;
    return planner.next(context, ...rest);
  };
  return {
    identity: { ...(planner.identity ?? {}), skill: 'recorded-script-with-planner-recovery' },
    stats: () => structuredClone(stats),
    next: async (context, ...rest) => {
      const elements = context.observation.elements;
      const last = context.lastResult;
      // Settle the script's own previous proposal.
      if (pending !== null) {
        if (last?.status === 'completed') { at = pending + 1; stats.scriptSteps += 1; }
        else if (last?.status === 'needs-replan') stats.retries += 1;
        pending = null;
      } else if (handed && last?.status === 'completed') {
        // Account for what the planner just did, so the script does not repeat it.
        if (last.kind === 'click') {
          const clicked = steps.findIndex((step, index) => index >= at && step.kind === 'click' && step.locator[1] === last.label);
          if (clicked >= 0) at = clicked + 1;
        } else if (typeof last.slot === 'string') suppliedByPlanner.add(last.slot);
      }
      handed = false;
      const holders = step => elements.filter(element => keyOf(element) === step.key);
      // Skip fills that are already done.
      while (at < steps.length && steps[at].kind !== 'click') {
        const step = steps[at], found = holders(step);
        const settled = found.length === 1 && typeof context.inputs?.[step.slot] === 'string' && found[0].value === context.inputs[step.slot];
        if (!settled && !suppliedByPlanner.has(step.slot)) break;
        at += 1; stats.skippedSteps += 1;
      }
      if (at >= steps.length) {
        if (stats.handBacks === 0) return { tool: 'finish', input: { summary: 'Skill script completed' } };
        return handBack('script-finished-after-recovery', context, rest);
      }
      const step = steps[at], found = holders(step);
      if (found.length !== 1) return handBack(found.length ? 'ambiguous-target' : 'missing-target', context, rest);
      if (step.kind !== 'click' && typeof context.inputs?.[step.slot] !== 'string') return handBack('missing-input-slot', context, rest);
      if (step.kind === 'click') {
        const remaining = new Set(steps.slice(at).map(later => later.key));
        const novel = elements.some(element => isWritable(element) && isEmpty(element)
          && !step.taught.has(keyOf(element)) && !remaining.has(keyOf(element)));
        if (novel) return handBack('new-empty-control-before-click', context, rest);
      }
      pending = at;
      return { tool: 'act', input: { kind: step.kind, handle: found[0].handle, ...(step.kind === 'click' ? {} : { slot: step.slot }) } };
    },
  };
}

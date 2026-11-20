// Fawn workspace differentiation — engineering investigation tool profiles for both arms.

import { completedUrl } from './fawn-agent.js';
import { controls } from './outline.js';

const DURATION = /active (\d+) min/;
const ASSIGNMENT = /(unassigned|investigated by ([\w-]+))/;
const mitigationIdOf = (url) => Number(/[?&]mitigation=(\d+)/.exec(url)?.[1]) || null;

function incidentFields(text) {
  const assigned = ASSIGNMENT.exec(text);
  return {
    service: ['Checkout', 'Auth', 'Storage'].find((service) => text.includes(` ${service} `) || text.includes(`| ${service} |`)) ?? null,
    durationMinutes: Number(DURATION.exec(text)?.[1] ?? 0),
    investigator: assigned?.[2] ?? null,
  };
}

function parseRunbookOutline(outline) {
  return outline.replace(/^Runbook guidance\s*\|\s*/, '').trim();
}

const FAWN_VIEWS = Object.freeze({
  queue: { regionGroups: ['.incident-row'] },
  incident: { regions: ['h1', '#runbook', '#mitigation-form', '#summary', '#reference', '#postmortem'] },
});

const FAWN_PARSERS = Object.freeze({
  queue: (regions, version) => ({
    incidents: Object.entries(regions).filter(([selector]) => selector.startsWith('#incident-')).map(([selector, outline]) => ({
      id: Number(selector.slice('#incident-'.length)),
      title: outline.split(' | ').find((part) => !part.startsWith('[')),
      ...incidentFields(outline),
      handle: controls(outline).find((control) => control.name === 'Claim incident')?.handle,
      region: selector,
      version,
    })),
  }),
  incident: (regions, version) => {
    const field = (region, name) => {
      const control = controls(regions[region] ?? '').find((candidate) => candidate.name === name);
      return control ? { handle: control.handle, value: control.value ?? '', region, version } : null;
    };
    const mitigate = controls(regions['#mitigation-form'] ?? '').find((control) => control.name === 'Record mitigation');
    const postmortem = controls(regions['#postmortem'] ?? '').find((control) => control.name === 'Download postmortem');
    return {
      runbook: parseRunbookOutline(regions['#runbook'] ?? ''),
      summary: field('#summary', 'summary'),
      reference: field('#reference', 'reference'),
      mitigate: mitigate ? { handle: mitigate.handle, version } : null,
      postmortem: postmortem ? { handle: postmortem.handle, version } : null,
    };
  },
});

const FAWN_ACTIONS = Object.freeze({
  claim: (target, options, { base, actionId, scoped, task, sequence }) => ({
    ...base,
    actionId: actionId('claim'),
    kind: 'click',
    ...scoped([target.region]),
    effect: { external: true, effectKey: `claim-incident:${task.id}:${target.id}:${sequence()}` },
    completion: { completedWhen: [{ kind: 'element-text-includes', selector: target.region, value: `investigated by ${task.agentName}` }] },
  }),
  fill: (target, { value }, { base, actionId, scoped }) => ({
    ...base,
    actionId: actionId('fill'),
    kind: 'fill',
    ...scoped([target.region]),
    params: { value },
  }),
  mitigate: (target, { incidentId, reference }, { base, actionId, scoped, task }) => ({
    ...base,
    actionId: actionId('mitigate'),
    kind: 'submit',
    ...scoped(['#mitigation-form']),
    effect: { external: true, effectKey: `mitigation:${task.id}`, ...(reference ? { externalIdempotencyKey: reference } : {}) },
    completion: { completedWhen: [{ kind: 'url-prefix', value: `${task.origin}/incidents/${incidentId}/mitigated` }] },
  }),
  download: (target, options, { base, actionId, scoped }) => ({
    ...base,
    actionId: actionId('download'),
    kind: 'download',
    ...scoped(['#postmortem']),
  }),
});

const investigationFawnProfile = Object.freeze({
  views: FAWN_VIEWS,
  parsers: FAWN_PARSERS,
  actions: FAWN_ACTIONS,
  results: {
    mitigate: (record) => ({ mitigationId: mitigationIdOf(completedUrl(record)) }),
    download: (record) => ({ sha256: record.evidence.effect.sha256 }),
  },
  interrupted: (task) => ({ effectKey: `mitigation:${task.id}`, idFrom: (record) => mitigationIdOf(completedUrl(record)) }),
});

const ROW_TEXT = /^\s*- text: (.+)$/;
const PARAGRAPH = /^\s*- paragraph(?:\s+\[[^\]]+\])*:\s*(.+)$/;
const BUTTON = /^\s*- button "([^"]+)" (?:\[[^\]]+\] )*\[ref=(e\d+)\]/;
const TEXTBOX = /^\s*- textbox "([^"]+)" (?:\[[^\]]+\] )*\[ref=(e\d+)\](?:: (.*))?$/;
const LINK = /^\s*- link "([^"]+)" \[ref=(e\d+)\]/;
const HEADING = /^\s*- '?heading "([^"]+)"/;

const PLAYWRIGHT_PARSERS = Object.freeze({
  queue: (lines) => ({
    incidents: lines.flatMap((line, index) => {
      const text = ROW_TEXT.exec(line)?.[1];
      const button = BUTTON.exec(lines[index + 1] ?? '');
      if (!text || button?.[1] !== 'Claim incident') return [];
      const link = lines.slice(Math.max(0, index - 3), index).map((candidate) => LINK.exec(candidate)).filter(Boolean).at(-1);
      return [{
        id: Number(/INC-(\d+)/.exec(link?.[1] ?? '')?.[1]) || null,
        titleLine: text,
        ...incidentFields(` ${text} `),
        ref: button[2],
      }];
    }),
  }),
  incident: (lines) => {
    const field = (name) => {
      const match = lines.map((line) => TEXTBOX.exec(line)).find((candidate) => candidate?.[1] === name);
      return match ? { ref: match[2], value: match[3] ?? '' } : null;
    };
    const runbookHeadingIndex = lines.findIndex((line) => HEADING.exec(line)?.[1] === 'Runbook guidance');
    const runbookLine = runbookHeadingIndex >= 0
      ? lines.slice(runbookHeadingIndex + 1, runbookHeadingIndex + 4).map((line) => PARAGRAPH.exec(line)?.[1]).find(Boolean) ?? ''
      : '';
    const mitigate = lines.map((line) => BUTTON.exec(line)).find((match) => match?.[1] === 'Record mitigation');
    const postmortem = lines.map((line) => LINK.exec(line)).find((match) => match?.[1] === 'Download postmortem');
    return {
      runbook: runbookLine.replace(/^"|"$/g, ''),
      summary: field('Mitigation'),
      reference: field('Reference'),
      mitigate: mitigate ? { ref: mitigate[2] } : null,
      postmortem: postmortem ? { ref: postmortem[2] } : null,
    };
  },
  mitigated: (lines) => {
    const heading = lines.map((line) => HEADING.exec(line)).find(Boolean)?.[1] ?? '';
    return { mitigationId: Number(/Mitigation (\d+) recorded/.exec(heading)?.[1]) || null, lines };
  },
  mitigations: (lines) => ({
    found: lines.some((line) => /Mitigations for incident/.test(HEADING.exec(line)?.[1] ?? '')),
    mitigations: lines.map((line) => /Mitigation (\d+); reference (\S+?)"?$/.exec(line)).filter(Boolean)
      .map(([, id, reference]) => ({ id: Number(id), reference })),
  }),
});

async function resolveInterruptedMitigation(agent, task, progress) {
  const current = PLAYWRIGHT_PARSERS.mitigated((await agent.snapshot()).full.split('\n'));
  if (current.mitigationId && current.lines.some((line) => line.includes(`Incident ${progress.incidentId};`))) {
    return { id: current.mitigationId };
  }
  await agent.navigate(`${task.origin}/incidents/${progress.incidentId}/mitigations`);
  const list = await agent.view('mitigations');
  if (list.found) {
    const match = list.mitigations.find((entry) => entry.reference === (progress.reference ?? 'none'));
    return match ? { id: match.id } : { retry: true };
  }
  if (progress.reference) return { retry: true };
  return { humanReview: true, reason: 'mitigation outcome unknown: no confirmation on page, no audit log, no idempotency' };
}

const PLAYWRIGHT_ACTS = Object.freeze({
  claim: (agent, target) => agent.tool('click', { ref: target.ref }, { consequential: true }),
  fill: (agent, target, { value }) => agent.tool('fill', { ref: target.ref, value }, { consequential: true }),
  download: (agent, target) => agent.tool('download', { ref: target.ref }, { consequential: true }),
  async mitigate(agent, target) {
    agent.requireAllowed((await agent.tool('formAction')).action);
    const recorded = await agent.tool('click', { ref: target.ref }, { consequential: true });
    return { mitigationId: mitigationIdOf(recorded.url) };
  },
});

const investigationPlaywrightProfile = Object.freeze({
  parsers: PLAYWRIGHT_PARSERS,
  act: PLAYWRIGHT_ACTS,
  resolveInterrupted: resolveInterruptedMitigation,
});

export { investigationFawnProfile, investigationPlaywrightProfile };

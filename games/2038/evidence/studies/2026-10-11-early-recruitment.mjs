import {readFile, writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {isDeepStrictEqual} from 'node:util';
import {SelectedRulesMatch} from '../../lab/environment/selected-rules-match.js';
import {createPlayerPolicy} from '../../lab/policies/policy-factory.js';
import {validateDecisionResponse} from '../../lab/contracts/decision-contract.js';
import {canonicalRulesVariant} from '../../lab/environment/rules-variant.js';
import {loadGameIdentity, sha256} from '../../lab/versioning/game-identity.js';
import {controlledAreas, nominalComputeCapacity} from '../../lab/rules/era-mandates.js';
import {verifyRelease} from '../../tasks/release-artifacts.mjs';
import {createRng, shuffle} from '../../web/src/engine.js';
import {subsets} from './2026-10-11-seat-diversity.mjs';
import {assertOutcome} from './2026-10-11-capacity-counterplay.mjs';
import {observeMatch} from './2026-10-11-reputation-counter.mjs';
import {summarizeOutcome} from './2026-10-11-plan-traces.mjs';

export const ROOT = 'early-recruitment-128-20261011-v1';
export const ARMS = ['parent', 'placement', 'recruit'];
const INPUTS = ['game-config', 'factions', 'headlines', 'projects', 'mandates'];
const FILES = ['2026-10-11-early-recruitment.mjs', '2026-10-11-early-recruitment-preregistration.md'];
const SELECTION = 'evidence/studies/simulation/2026-10-11-seat-diversity-greedy-diversity-selection.json';
const SELECTION_HASH = 'f879402e2d46047a879a9d0a8284adce7b5c09af139a30b85cfbcb6ea3701932';
const rotate = (xs, n) => xs.map((_, i) => xs[(i + n) % xs.length]);
const holdings = p => Object.fromEntries(['runway', 'compute', 'capability', 'reputation', 'customers'].map(k => [k, p[k]]));
const mean = xs => xs.reduce((s, x) => s + x, 0) / xs.length;

export function scenarios(count, smoke = false) {
  if (![3, 4, 5].includes(count)) throw new RangeError('Use a supported study count.');
  const rows = [];
  for (const [subset, ids] of subsets([0, 1, 2, 3, 4, 5], count).entries())
    for (const mode of ['fixed', 'variable']) for (let repeat = 0; repeat < (count === 4 ? 2 : 1); repeat++) {
      const setup = `${ROOT}:${smoke ? 'smoke' : 'holdout'}:${count}:${subset}:${mode}:${repeat}`;
      const order = shuffle(ids, createRng(`${setup}:institutions`));
      for (let seat = 0; seat < count; seat++) for (let rotation = 0; rotation < count; rotation++)
        rows.push({count, subset, mode, repeat, seat, rotation, institutions: rotate(order, rotation),
          seed: `${setup}:${seat}:${rotation}`});
      if (smoke) return rows;
    }
  return rows;
}

// Only public positions, holdings, legal resolutions and the parent's resource prices.
// This one-production heuristic is not a search over decks or future match states.
export function placementValue(packet, decision, config, prices) {
  const self = structuredClone(packet.observation.self), p = decision.parameters;
  const tile = id => packet.observation.board.find(t => t.instanceId === id);
  const acting = self.pieces.find(o => o.id === p.pieceId);
  if (!acting) return -Infinity;
  acting.tileId = p.destinationId;
  if (p.mode === 'reassign') self.pieces.find(o => o.id === p.otherAgentId).tileId = p.otherAreaId;
  if (p.equipOrgId) self.pieces.find(o => o.id === p.equipOrgId).equipped = true;
  if (p.mode === 'recruit') self.pieces.push({tileId: p.destinationId, equipped: false});
  const available = {...self};
  available.runway -= p.actualRunwayCost ?? (p.mode === 'recruit' ? config.actionEffects.organize.recruitCost : 0);
  let value = 0;
  for (const org of self.pieces) {
    const t = tile(org.tileId); if (!t) continue;
    const k = t.yield.resource, amount = t.yield.amount * (org.equipped ? 2 : 1);
    const actual = Math.max(0, Math.min(amount, config.resources[k].cap - available[k]));
    value += actual * (prices[k] ?? 1); available[k] += actual;
  }
  return value;
}

export class RecruitmentPlan {
  constructor(parent, resolutions, config, arm) {
    this.parent = parent; this.resolutions = resolutions; this.config = config; this.arm = arm;
    this.pending = null; this.recruitAttempted = false; this.setupAttempted = false; this.decisions = [];
  }
  best(packet, choices) {
    return choices.map(d => ({d, value: placementValue(packet, d, this.config,
      this.parent.profile.strategy.resourceValues)})).sort((a, b) => b.value - a.value ||
        a.d.decisionId.localeCompare(b.d.decisionId))[0]?.d;
  }
  async decide(packet) {
    const ordinary = await this.parent.decide(packet), stage = packet.requestId.split(':').at(-2);
    let selected = packet.legalDecisions.find(d => d.decisionId === ordinary.decision.decisionId), reason = 'parent';
    if (stage === 'select' && this.arm === 'recruit') {
      this.pending = null;
      const third = packet.observation.self.pieces.find(o => o.id === `s${packet.seat}-agent-3`);
      if (!this.recruitAttempted) {
        this.recruitAttempted = true;
        const choices = this.resolutions('organize').filter(d => d.parameters.mode === 'recruit');
        if (packet.round === 1 && packet.cycle === 1 && choices.length)
          this.pending = {decision: this.best(packet, choices), reason: 'early_recruit'};
      } else if (third && !this.setupAttempted && packet.round === 1) {
        this.setupAttempted = true;
        const tile = id => packet.observation.board.find(t => t.instanceId === id);
        const productive = t => t?.yield.resource === 'compute' && t.yield.amount === 2;
        if (!productive(tile(third.tileId))) {
          const direct = this.resolutions('build').filter(d => d.parameters.pieceId === third.id &&
            d.parameters.equipOrgId === third.id && productive(tile(d.parameters.destinationId)));
          const assign = this.resolutions('organize').filter(d => d.parameters.mode === 'reassign' &&
            d.parameters.otherAgentId === third.id && productive(tile(d.parameters.otherAreaId)));
          const chosen = this.best(packet, direct.length ? direct : assign);
          if (chosen) this.pending = {decision: chosen, reason: direct.length ? 'equip_extra_org' : 'position_extra_org'};
        }
      }
      if (this.pending) {
        selected = packet.legalDecisions.find(d => d.actionId === this.pending.decision.actionId);
        if (!selected) throw new Error('Planned resolution has no legal Action selection.');
        reason = this.pending.reason;
      }
    }
    if (stage === 'resolve' && this.arm !== 'parent') {
      if (this.pending) {
        selected = packet.legalDecisions.find(d => d.decisionId === this.pending.decision.decisionId);
        if (!selected) throw new Error('Planned resolution ceased to be legal.');
        reason = this.pending.reason; this.pending = null;
      } else {
        // Keep the parent's Action and mode. Choose its productive position;
        // Build may equip a different Org for the same ordinary printed cost.
        const choices = packet.legalDecisions.filter(d => d.actionId === selected.actionId &&
          d.parameters.mode === selected.parameters.mode);
        selected = this.best(packet, choices); reason = 'productive_resolution';
      }
    }
    if (['select', 'resolve'].includes(stage)) this.decisions.push({round: packet.round, cycle: packet.cycle,
      stage, reason, parentDecision: ordinary.decision.decisionId, decision: selected.decisionId,
      action: selected.actionId, parameters: selected.parameters, before: holdings(packet.observation.self),
      pieces: packet.observation.self.pieces, legalDecisionIds: packet.legalDecisions.map(d => d.decisionId)});
    return reason === 'parent' ? ordinary : {decision: validateDecisionResponse(packet,
      {decisionId: selected.decisionId, rationale: reason}), receipt: {...ordinary.receipt,
        studyArm: this.arm, studyReason: reason, parentDecision: ordinary.decision.decisionId}};
  }
}

export function observeProduction(match) {
  const rows = [], produce = match.produceAll.bind(match), add = match.addResource.bind(match);
  let queue = null;
  match.addResource = (p, key, amount) => {
    const before = p[key], actual = add(p, key, amount);
    if (queue) {
      const source = queue.shift();
      if (!source || source.seat !== p.seat || source.resource !== key || source.nominal !== amount)
        throw new Error('Production source order changed.');
      rows.push({...source, round: match.round, before, after: p[key], actual, capLoss: amount - actual});
    }
    return actual;
  };
  match.produceAll = async () => {
    queue = match.initiativeOrder().flatMap(seat => {
      const p = match.players[seat], sources = [];
      if (match.hasFactionAbility(p, 'the_shovels')) sources.push({seat, source: 'faction', resource: 'runway',
        nominal: Math.min(2, match.players.filter(x => x.seat !== seat && x.pieces.some(o => o.equipped)).length)});
      for (const org of p.pieces.filter(o => o.tileId)) {
        const t = match.board.find(t => t.instanceId === org.tileId);
        sources.push({seat, source: 'org', orgId: org.id, tileId: org.tileId, equipped: org.equipped,
          resource: t.yield.resource, nominal: t.yield.amount * (org.equipped ? 2 : 1)});
      }
      sources.push({seat, source: 'customers', resource: 'runway', nominal: p.customers}); return sources;
    });
    await produce(); if (queue.length) throw new Error('Missing production call.'); queue = null;
  };
  return rows;
}

export async function playArm(input, block, roster, arm, projection = 'batch', observe = true) {
  const match = new SelectedRulesMatch({config: input['game-config'],
    factions: block.institutions.map(i => input.factions.factions[i]), profiles: roster,
    backends: roster.map(() => 'greedy'), headlines: input.headlines, projects: input.projects,
    mandates: input.mandates, seed: block.seed, playerCount: block.count, mandateMode: block.mode,
    projection, recordReplay: false});
  const policies = roster.map(p => createPlayerPolicy(p, 'greedy', {rosterProfileIds: roster.map(p => p.id)}));
  const policy = new RecruitmentPlan(policies[block.seat], action => match.legalResolutions(block.seat, action),
    input['game-config'], arm);
  policies[block.seat] = policy;
  const sources = observe ? observeProduction(match) : null, trace = observe ? observeMatch(match) : null;
  if (observe) {
    const research = match.research.bind(match);
    match.research = async (policies, seat, decision) => {
      const before = holdings(match.players[seat]);
      await research(policies, seat, decision);
      trace.resolutions.push({round: match.round, cycle: match.cycle, seat, action: 'research',
        parameters: structuredClone(decision.parameters), before, after: holdings(match.players[seat]),
        research: structuredClone(match.players[seat].metrics.researchCapability.at(-1))});
    };
  }
  const result = await match.play(policies); assertOutcome(match, result);
  const outcome = summarizeOutcome(result, input['game-config']);
  if (observe && (trace.production.length !== 4 || trace.reviews.length !== 4 ||
      policy.decisions.filter(d => d.stage === 'select').length !== 12)) throw new Error('Incomplete trace.');
  const focal = match.players[block.seat];
  return {outcome, trace, sources, decisions: policy.decisions,
    final: {pieces: structuredClone(focal.pieces), controlledAreas: controlledAreas(match, focal),
      nominalComputeCapacity: nominalComputeCapacity(match, focal), objectives: match.finalObjectives()}};
}

// Range-scaled Theorem 11 bounds, the same fixed-look method as the prior study.
export function interval(xs, bound = 1) {
  if (xs.length < 2 || xs.some(x => !Number.isFinite(x) || Math.abs(x) > bound)) throw new RangeError('Invalid paired observations.');
  const n = xs.length, estimate = mean(xs), variance = xs.reduce((s, x) => s + (x - estimate) ** 2, 0) / (n - 1);
  const log = Math.log(4 * 12 / 0.05), radius = Math.sqrt(2 * variance * log / n) + 14 * bound * log / (3 * (n - 1));
  return {n, mean: estimate, variance, radius, lower: Math.max(-bound, estimate - radius),
    upper: Math.min(bound, estimate + radius), comparisons: 12, familyAlpha: 0.05};
}

export function summarize(rows) {
  const focal = (r, arm) => r.arms[arm].outcome.players[r.block.seat];
  return {games: rows.length * 3, scenarios: rows.length,
    arms: Object.fromEntries(ARMS.map(arm => [arm, {winCredit: mean(rows.map(r => focal(r, arm).winCredit)),
      score: mean(rows.map(r => focal(r, arm).score))}])),
    effects: Object.fromEntries(['parent', 'placement'].map(control => [control, {
      winCredit: interval(rows.map(r => focal(r, 'recruit').winCredit - focal(r, control).winCredit)),
      score: interval(rows.map(r => focal(r, 'recruit').score - focal(r, control).score), 40)}]))};
}

export async function runStudy(count, smoke = false) {
  const blocks = scenarios(count, smoke);
  if (execFileSync('git', ['status', '--porcelain'], {encoding: 'utf8'}).trim()) throw new Error('Clean committed source required.');
  await verifyRelease(process.cwd());
  const bytes = await readFile(SELECTION);
  if (sha256(bytes) !== SELECTION_HASH) throw new Error('Frozen opponent selection changed.');
  const frozen = JSON.parse(bytes), selected = frozen.selected;
  const parent = selected.find(p => p.id === 'balanced_operator');
  const order = ['agi_candidate', 'power_broker', 'market_maximalist'];
  const rivals = (count === 3 ? ['agi_candidate', 'market_maximalist'] : count === 4 ? order : [...order, 'balanced_operator'])
    .map(id => selected.find(p => p.id === id));
  if (!parent || rivals.some(p => !p)) throw new Error('Frozen field is incomplete.');
  const inputBytes = await Promise.all(INPUTS.map(n => readFile(`dist/runtime/${n}.json`)));
  const input = Object.fromEntries(INPUTS.map((n, i) => [n, JSON.parse(inputBytes[i])]));
  const options = {profiles: selected, backends: ['greedy'], policyProjection: 'batch',
    rulesVariant: canonicalRulesVariant(input['game-config']), experimentKind: 'early_recruitment',
    experimentConfiguration: {root: ROOT, count, smoke, arms: ARMS}};
  const identity = await loadGameIdentity(options);
  if (!isDeepStrictEqual(identity.game, frozen.identity.game) || !isDeepStrictEqual(identity.engine, frozen.identity.engine))
    throw new Error('Frozen game/engine changed.');
  const fileHashes = Object.fromEntries(await Promise.all(FILES.map(async f => [f, sha256(await readFile(`evidence/studies/${f}`))])));
  const output = `evidence/studies/simulation/2026-10-11-early-recruitment-${count}${smoke ? '-smoke' : ''}-raw.json`;
  const raw = {status: 'running', evidenceType: 'simulation', root: ROOT, count, smoke, identity, selected,
    generatedAt: new Date().toISOString(), selectionHash: sha256(bytes), fileHashes,
    inputHashes: Object.fromEntries(INPUTS.map((n, i) => [n, sha256(inputBytes[i])])), rows: []};
  await writeFile(output, JSON.stringify({status: 'running', identity}) + '\n', {flag: 'wx'});
  try {
    for (const block of blocks) {
      const roster = rotate([parent, ...rivals], (count - block.seat) % count);
      const row = {block, rosterIds: roster.map(p => p.id), arms: {}}; raw.rows.push(row);
      for (const arm of ARMS) {
        raw.active = {seed: block.seed, arm}; row.arms[arm] = await playArm(input, block, roster, arm);
        if (smoke) {
          const control = await playArm(input, block, roster, arm, 'rich', false);
          if (!isDeepStrictEqual(row.arms[arm].outcome, control.outcome) ||
              !isDeepStrictEqual(row.arms[arm].final, control.final)) throw new Error('Rich/unobserved parity failed.');
        }
      }
      if (raw.rows.length % 40 === 0) process.stderr.write(`${count}: ${raw.rows.length}/${blocks.length} matched scenarios complete\n`);
    }
    if (!isDeepStrictEqual(identity, await loadGameIdentity(options))) throw new Error('Identity drift.');
    if (sha256(await readFile(SELECTION)) !== raw.selectionHash) throw new Error('Selection drift.');
    for (const f of FILES) if (sha256(await readFile(`evidence/studies/${f}`)) !== fileHashes[f]) throw new Error('Study source drift.');
    raw.summary = summarize(raw.rows); delete raw.active; raw.status = smoke ? 'smoke_only' : 'complete';
  } catch (error) {raw.status = 'failed'; raw.error = {message: error.message, stack: error.stack}; throw error;}
  finally {await writeFile(output, JSON.stringify(raw) + '\n');}
  console.log(JSON.stringify({count, smoke, status: raw.status, output, sha256: sha256(await readFile(output)), summary: raw.summary}));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href)
  await runStudy(Number(process.argv[process.argv.indexOf('--players') + 1]), process.argv.includes('--smoke'));

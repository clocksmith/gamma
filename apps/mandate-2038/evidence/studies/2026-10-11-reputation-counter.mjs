import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {isDeepStrictEqual} from 'node:util';
import {SelectedRulesMatch} from '../../lab/environment/selected-rules-match.js';
import {canonicalRulesVariant} from '../../lab/environment/rules-variant.js';
import {createPlayerPolicy} from '../../lab/policies/policy-factory.js';
import {validateDecisionResponse} from '../../lab/contracts/decision-contract.js';
import {loadGameIdentity, sha256} from '../../lab/versioning/game-identity.js';
import {verifyRelease} from '../../tasks/release-artifacts.mjs';
import {makeBlocks, rosterFor, assertOutcome} from './2026-10-11-capacity-counterplay.mjs';

export const ROOT = 'reputation-counter-128-20261011-v1';
const INPUTS = ['game-config', 'factions', 'headlines', 'projects', 'mandates'];
const FILES = ['2026-10-11-reputation-counter.mjs', '2026-10-11-reputation-counter-preregistration.md'];
const SELECTION_HASHES = {greedy: 'bc71ae724ddb1fdc529196ace9e4a1667e651c6f9648d25b28347bebbbd19429',
  weighted: '016fe50544dc8528cee15f578937a4c0193165849ce5ce27b5b49b82e1fc87ae'};
const HOLDINGS = ['runway', 'compute', 'capability', 'reputation', 'customers'];
const mean = xs => xs.reduce((s, x) => s + x, 0) / xs.length;
const holdings = p => Object.fromEntries(HOLDINGS.map(k => [k, p[k]]));

export function blocksFor(stage, count, backend, repetitions) {
  return makeBlocks(stage, count, backend, repetitions).map(b => ({...b,
    seed: b.seed.replace('capacity-counterplay-128-20261011-v1', ROOT)}));
}

// Study-local policy: no new default persona or runtime treatment.
export class ReputationCounter {
  constructor(parent) { this.parent = parent; this.decisions = []; }
  async decide(packet) {
    const ordinary = await this.parent.decide(packet);
    const influence = packet.legalDecisions.find(d => d.actionId === 'influence' &&
      d.consequences?.stage === 'action_selection' && d.consequences.resolvableWithoutTrade === true);
    const triggered = packet.observation.self.reputation <= 1 && Boolean(influence);
    if (!triggered) return ordinary;
    const changed = ordinary.decision.decisionId !== influence.decisionId;
    this.decisions.push({round: packet.round, cycle: packet.cycle,
      reputation: packet.observation.self.reputation,
      parentDecision: ordinary.decision.decisionId, decision: influence.decisionId, changed});
    return {decision: validateDecisionResponse(packet, {decisionId: influence.decisionId,
      rationale: 'At 0/1 Reputation, take reachable Influence.'}),
    receipt: {...ordinary.receipt, studyCondition: 'low_reputation_influence',
      parentDecision: ordinary.decision.decisionId, changed}};
  }
}

export function interval(xs) {
  if (!xs.length || xs.some(x => !Number.isFinite(x) || x < -1 || x > 1))
    throw new RangeError('Nonempty bounded winner-credit differences required.');
  const estimate = mean(xs), radius = Math.sqrt(2 * Math.log(2 * 12 / 0.05) / xs.length);
  return {n: xs.length, mean: estimate, lower: Math.max(-1, estimate - radius),
    upper: Math.min(1, estimate + radius), radius, method: 'fixed-look Hoeffding; 12 effects; family alpha 0.05'};
}

export function observeMatch(match) {
  const trace = {production: [], resolutions: [], reviews: []};
  const produce = match.produceAll.bind(match);
  match.produceAll = async () => {
    const rows = match.players.map(p => ({seat: p.seat, before: holdings(p),
      orgs: p.pieces.map(org => {
        const tile = match.board.find(t => t.instanceId === org.tileId);
        return {id: org.id, tileId: org.tileId, equipped: org.equipped,
          action: tile?.actionId ?? null, resource: tile?.yield.resource ?? null,
          nominalBase: tile?.yield.amount ?? 0,
          nominalEquipmentBonus: org.equipped ? tile?.yield.amount ?? 0 : 0};
      })}));
    await produce();
    rows.forEach(row => {row.after = holdings(match.players[row.seat]);
      row.actualDelta = Object.fromEntries(HOLDINGS.map(k => [k, row.after[k] - row.before[k]]));});
    trace.production.push({round: match.round, players: rows});
  };
  const resolve = match.applyResolution.bind(match);
  match.applyResolution = (seat, decision) => {
    const before = holdings(match.players[seat]);
    const applied = resolve(seat, decision);
    trace.resolutions.push({round: match.round, cycle: match.cycle, seat,
      action: applied.actionId, parameters: structuredClone(applied.parameters),
      before, after: holdings(match.players[seat])});
    return applied;
  };
  const audit = match.audit.bind(match);
  match.audit = async () => {
    const before = match.players.map(holdings);
    await audit();
    trace.reviews.push({round: match.round, players: match.players.map((p, seat) => ({seat,
      reputation: before[seat].reputation, runwayLoss: before[seat].runway - p.runway}))});
  };
  return trace;
}

export async function playObserved(input, block, roster, candidate, projection = 'batch', observed = true) {
  const policies = roster.map(p => createPlayerPolicy(p, block.backend,
    {rosterProfileIds: roster.map(p => p.id)}));
  if (candidate) policies[block.responderSeat] = new ReputationCounter(policies[block.responderSeat]);
  const match = new SelectedRulesMatch({config: input['game-config'],
    factions: Array.from({length: block.count}, (_, s) => input.factions.factions[(block.faction + s - block.seat + 6) % 6]),
    profiles: roster, backends: Array(block.count).fill(block.backend), headlines: input.headlines,
    projects: input.projects, mandates: input.mandates, seed: block.seed, playerCount: block.count,
    mandateMode: block.mode, projection, recordReplay: false});
  const trace = observed ? observeMatch(match) : null;
  const result = await match.play(policies);
  assertOutcome(match, result);
  const players = [...result.standings].sort((a, b) => a.seat - b.seat).map(p => {
    const scoreParts = {capability: p.capability * input['game-config'].scoring.capability,
      customers: p.customers * match.rulesVariant.customerPoints,
      reputation: p.reputation * input['game-config'].scoring.reputation,
      agi: p.agiDeclared ? input['game-config'].scoring.agi : 0,
      objectives: Object.values(p.metrics.mandatesWon).reduce((s, x) => s + x, 0)};
    if (Object.values(scoreParts).reduce((s, x) => s + x, 0) !== p.score)
      throw new Error('Score components do not reconcile.');
    return {seat: p.seat, factionId: p.factionId, profileId: p.profileId, score: p.score, scoreParts,
      winCredit: result.winnerSeats.includes(p.seat) ? 1 / result.winnerSeats.length : 0,
      holdings: holdings(p), equippedOrgs: p.equippedOrgs, orgCount: match.players[p.seat].pieces.length,
      agiDeclared: p.agiDeclared, actions: p.metrics.actions, research: p.metrics.researchCapability,
      reviewHits: p.metrics.reputationReviewHits, forcedNoOps: p.metrics.forcedNoOps,
      policyFallbacks: p.metrics.policyFallbacks};
  });
  return {outcome: {winnerSeats: result.winnerSeats, players, trades: result.matchMetrics.trades},
    trace, counterDecisions: candidate ? policies[block.responderSeat].decisions : []};
}

export function summarize(rows) {
  return Object.fromEntries([3, 4, 5].map(count => {
    const cases = rows.filter(r => r.block.count === count);
    const roles = {capacity: 'seat', responder: 'responderSeat'};
    const arms = Object.fromEntries(['control', 'candidate'].map(arm => [arm,
      Object.fromEntries(Object.entries(roles).map(([role, key]) => {
        const ps = cases.map(r => r.arms[arm].outcome.players[r.block[key]]);
        return [role, {winCredit: mean(ps.map(p => p.winCredit)), score: mean(ps.map(p => p.score)),
          scoreParts: Object.fromEntries(Object.keys(ps[0].scoreParts).map(k => [k, mean(ps.map(p => p.scoreParts[k]))])),
          actions: Object.fromEntries(['fund', 'research', 'build', 'organize', 'deploy', 'influence']
            .map(k => [k, mean(ps.map(p => p.actions[k] || 0))])),
          equippedOrgs: mean(ps.map(p => p.equippedOrgs)), orgCount: mean(ps.map(p => p.orgCount)),
          reviewHits: mean(ps.map(p => p.reviewHits)), agiRate: mean(ps.map(p => Number(p.agiDeclared)))}];
      }))]));
    const effect = (key, sign) => interval(cases.map(r => sign * (r.arms.candidate.outcome.players[r.block[key]].winCredit -
      r.arms.control.outcome.players[r.block[key]].winCredit)));
    const noOps = Object.fromEntries(['control', 'candidate'].map(arm => [arm,
      cases.reduce((s, r) => s + r.arms[arm].outcome.players.reduce((n, p) => n + p.forcedNoOps, 0), 0) /
      (cases.length * count * 12)]));
    return [count, {blocks: cases.length, arms, noOps,
      effects: {responderGain: effect('responderSeat', 1), capacitySuppression: effect('seat', -1)},
      changedDecisions: cases.reduce((s, r) => s + r.arms.candidate.counterDecisions.filter(d => d.changed).length, 0),
      triggeredDecisions: cases.reduce((s, r) => s + r.arms.candidate.counterDecisions.length, 0)}];
  }));
}

export async function runStudy({backend, smoke = false}) {
  if (!Object.hasOwn(SELECTION_HASHES, backend)) throw new TypeError('Use greedy or weighted.');
  if (execFileSync('git', ['status', '--porcelain'], {encoding: 'utf8'}).trim()) throw new Error('Clean source required.');
  await verifyRelease(process.cwd());
  const inputBytes = await Promise.all(INPUTS.map(n => readFile(`dist/runtime/${n}.json`)));
  const input = Object.fromEntries(INPUTS.map((n, i) => [n, JSON.parse(inputBytes[i])]));
  const selectionBytes = await readFile(`evidence/studies/simulation/2026-10-11-capacity-counterplay-${backend}-selection.json`);
  if (sha256(selectionBytes) !== SELECTION_HASHES[backend]) throw new Error('Frozen selection changed.');
  const frozen = JSON.parse(selectionBytes);
  const {selection} = frozen;
  const profiles = [selection.champion, ...selection.trainedRivals];
  const identityOptions = {rulesVariant: canonicalRulesVariant(input['game-config']), profiles, backends: [backend],
    policyProjection: 'batch', experimentKind: 'reputation_counter', experimentConfiguration: {root: ROOT, smoke}};
  const identity = await loadGameIdentity(identityOptions);
  if (identity.provenance.sourceDirty !== false) throw new Error('Dirty identity.');
  if (!isDeepStrictEqual(identity.game, frozen.identity.game) || !isDeepStrictEqual(identity.engine, frozen.identity.engine))
    throw new Error('Frozen selection belongs to different game or engine bytes.');
  const fileHashes = Object.fromEntries(await Promise.all(FILES.map(async f => [f, sha256(await readFile(`evidence/studies/${f}`))])));
  const raw = {evidenceType: 'simulation', root: ROOT, backend, smoke, generatedAt: new Date().toISOString(), identity,
    fileHashes, selectionHash: sha256(selectionBytes), inputHashes: Object.fromEntries(INPUTS.map((n, i) => [n, sha256(inputBytes[i])])),
    games: 0, confirmation: [], status: 'running'};
  await mkdir('evidence/studies/simulation', {recursive: true});
  const output = `evidence/studies/simulation/2026-10-11-reputation-counter-${backend}${smoke ? '-smoke' : ''}-raw.json`;
  await writeFile(output, JSON.stringify({status: 'running', identity}) + '\n', {flag: 'wx'});
  try {
    for (const count of [3, 4, 5]) {
      const blocks = smoke ? blocksFor('smoke', count, backend, 1).slice(0, 1)
        : blocksFor('confirmation', count, backend, count === 4 ? 16 : 4);
      for (const block of blocks) {
        const roster = rosterFor(block, selection.champion, selection.trainedRivals, selection.responderParent);
        const row = {block, rosterIds: roster.map(p => p.id), arms: {}};
        raw.confirmation.push(row);
        for (const [arm, candidate] of [['control', false], ['candidate', true]]) {
          raw.activeGame = {block, arm};
          row.arms[arm] = await playObserved(input, block, roster, candidate);
          raw.games++;
          if (smoke) {
            const rich = await playObserved(input, block, roster, candidate, 'rich'); raw.games++;
            if (!isDeepStrictEqual(row.arms[arm], rich)) throw new Error('Rich/batch disagreement.');
          }
        }
        if (raw.games % 96 === 0) process.stderr.write(`${backend}: ${raw.games} games complete\n`);
      }
    }
    if (!isDeepStrictEqual(identity, await loadGameIdentity(identityOptions))) throw new Error('Identity drift.');
    for (const f of FILES) if (sha256(await readFile(`evidence/studies/${f}`)) !== fileHashes[f]) throw new Error('Protocol drift.');
    if (sha256(await readFile(`evidence/studies/simulation/2026-10-11-capacity-counterplay-${backend}-selection.json`)) !== raw.selectionHash)
      throw new Error('Selection drift.');
    raw.summary = summarize(raw.confirmation);
    raw.gates = {primary: Object.values(raw.summary[4].effects).every(e => e.lower > 0.04),
      guards: [3, 5].every(n => raw.summary[n].effects.responderGain.lower > -0.05),
      noOp: Object.values(raw.summary).every(s => Object.values(s.noOps).every(x => x <= 0.03))};
    delete raw.activeGame;
    raw.status = smoke ? 'smoke_only' : 'complete';
  } catch (e) {raw.status = 'failed'; raw.error = {message: e.message, stack: e.stack}; throw e;}
  finally {
    await writeFile(output, JSON.stringify(raw) + '\n');
    process.stderr.write(`${backend}: retained ${raw.games} games, ${raw.status}, ${output}\n`);
  }
  console.log(JSON.stringify({backend, smoke, games: raw.games, gates: raw.gates, output,
    sha256: sha256(await readFile(output)), summary: raw.summary}));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const i = process.argv.indexOf('--backend');
  await runStudy({backend: process.argv[i + 1], smoke: process.argv.includes('--smoke')});
}

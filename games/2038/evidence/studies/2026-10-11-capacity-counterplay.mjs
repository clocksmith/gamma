import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {isDeepStrictEqual} from 'node:util';
import {SelectedRulesMatch} from '../../lab/environment/selected-rules-match.js';
import {canonicalRulesVariant} from '../../lab/environment/rules-variant.js';
import {createPlayerPolicy} from '../../lab/policies/policy-factory.js';
import {mutateStrategy} from '../../lab/runner/optimization-runner.js';
import {loadGameIdentity, fingerprintObject, sha256} from '../../lab/versioning/game-identity.js';
import {verifyRelease} from '../../tasks/release-artifacts.mjs';

export const ROOT = 'capacity-counterplay-128-20261011-v1';
export const ARMS = ['authored', 'field', 'equal_budget', 'counter', 'adapted', 'mirror'];
export const EFFECTS = {
  fieldSuppression: ['authored', 'field', 'focal'],
  generalRecovery: ['equal_budget', 'field', 'focal'],
  counterOwnGain: ['counter', 'equal_budget', 'responder'],
  capacitySuppression: ['equal_budget', 'counter', 'focal'],
  adaptiveRecovery: ['adapted', 'counter', 'focal'],
  responderRetention: ['adapted', 'equal_budget', 'responder']
};
const INPUTS = ['game-config', 'factions', 'headlines', 'projects', 'mandates', 'player-strategies'];
const STUDY_FILES = ['2026-10-11-capacity-counterplay.mjs', '2026-10-11-capacity-counterplay-preregistration.md'];
const mean = xs => xs.reduce((sum, x) => sum + x, 0) / xs.length;

export function pairedInterval(xs) {
  if (!xs.length || xs.some(x => !Number.isFinite(x) || x < -1 || x > 1))
    throw new RangeError('Winner-credit differences require nonempty bounded observations.');
  const estimate = mean(xs);
  const radius = Math.sqrt(2 * Math.log(2 * 36 / 0.05) / xs.length);
  return {n: xs.length, mean: estimate, lower: Math.max(-1, estimate - radius),
    upper: Math.min(1, estimate + radius), method: 'fixed-look Hoeffding; Bonferroni 36 effects, family alpha 0.05'};
}

export function makeBlocks(stage, count, backend, repetitions) {
  const blocks = [];
  for (let faction = 0; faction < 6; faction++)
    for (let seat = 0; seat < count; seat++)
      for (const mode of ['variable', 'fixed'])
        for (let repeat = 0; repeat < repetitions; repeat++)
          blocks.push({stage, count, backend, faction, seat, mode, repeat,
            responderSeat: (seat + 1 + (faction + repeat + Number(mode === 'fixed')) % (count - 1)) % count,
            seed: `${ROOT}:${stage}:${backend}:${count}:${faction}:${seat}:${mode}:${repeat}`});
  return blocks;
}

export function rosterFor(block, focal, pool, replacement = null) {
  const {count, seat, faction, repeat, mode, responderSeat} = block;
  const offset = (faction + repeat + Number(mode === 'fixed')) % pool.length;
  const rotated = Array.from({length: pool.length}, (_, i) => pool[(offset + i) % pool.length]);
  const ordered = replacement
    ? [replacement, ...rotated.filter(p => p.id !== replacement.id)]
    : rotated;
  const roster = Array(count);
  roster[seat] = focal;
  // Keep the responder parent's identity at the same seat in every paired arm.
  const seats = [responderSeat, ...Array.from({length: count}, (_, i) => i)
    .filter(i => i !== seat && i !== responderSeat)];
  seats.forEach((s, i) => { roster[s] = ordered[i % ordered.length]; });
  return roster;
}

export function candidatesFor(profile, stage, backend) {
  return [structuredClone(profile), ...Array.from({length: 3}, (_, i) =>
    mutateStrategy(profile, `${ROOT}:${stage}:${backend}:candidate:${i}`, {magnitude: 0.75}))];
}

export function assertOutcome(match, result) {
  if (!match.complete || result.standings.length !== match.playerCount || !result.winnerSeats.length)
    throw new Error('Incomplete game or missing winner.');
  const ids = match.players.flatMap(p => p.pieces.map(org => org.id));
  if (new Set(ids).size !== ids.length) throw new Error('Duplicate Org ownership.');
  for (const p of result.standings) {
    if (['runway', 'compute', 'capability', 'reputation', 'customers', 'score']
      .some(k => !Number.isFinite(p[k]) || p[k] < 0) || p.metrics.policyFallbacks !== 0)
      throw new Error('Invalid holdings, score, or policy fallback.');
  }
  for (const p of match.players) for (const org of p.pieces)
    if (org.tileId && !match.board.some(t => t.instanceId === org.tileId))
      throw new Error('Invalid Org position.');
  if (result.decisionProtocol.immediateTradePackets > result.decisionProtocol.immediateTradePacketCeiling)
    throw new Error('Trade protocol exceeded its bound.');
}

export async function playBlock(input, block, roster, projection = 'batch') {
  const factions = Array.from({length: block.count}, (_, s) =>
    input.factions.factions[(block.faction + s - block.seat + 6) % 6]);
  const policies = roster.map(profile => createPlayerPolicy(profile, block.backend,
    {rosterProfileIds: roster.map(p => p.id)}));
  const match = new SelectedRulesMatch({config: input['game-config'], factions,
    profiles: roster, backends: Array(block.count).fill(block.backend),
    headlines: input.headlines, projects: input.projects, mandates: input.mandates,
    seed: block.seed, playerCount: block.count, mandateMode: block.mode,
    projection, recordReplay: false});
  const result = await match.play(policies);
  assertOutcome(match, result);
  return {winnerSeats: result.winnerSeats, trades: result.matchMetrics.trades,
    players: [...result.standings].sort((a, b) => a.seat - b.seat).map(p => ({
      seat: p.seat, factionId: p.factionId, profileId: p.profileId, score: p.score,
      winCredit: result.winnerSeats.includes(p.seat) ? 1 / result.winnerSeats.length : 0,
      holdings: Object.fromEntries(['runway', 'compute', 'capability', 'reputation', 'customers'].map(k => [k, p[k]])),
      equippedOrgs: p.equippedOrgs, agiDeclared: p.agiDeclared,
      actions: p.metrics.actions, forcedNoOps: p.metrics.forcedNoOps,
      policyFallbacks: p.metrics.policyFallbacks
    }))};
}

function playerSummary(rows, arm, role) {
  const players = rows.map(r => r.arms[arm].players[role === 'focal' ? r.block.seat : r.block.responderSeat]);
  const actions = {};
  for (const p of players) for (const [k, n] of Object.entries(p.actions)) actions[k] = (actions[k] || 0) + n;
  const actionCount = Object.values(actions).reduce((sum, n) => sum + n, 0);
  return {n: players.length, winCredit: mean(players.map(p => p.winCredit)),
    meanScore: mean(players.map(p => p.score)), actions,
    agiRate: mean(players.map(p => Number(p.agiDeclared))),
    meanEquippedOrgs: mean(players.map(p => p.equippedOrgs)),
    forcedNoOpRate: actionCount ? players.reduce((sum, p) => sum + p.forcedNoOps, 0) / actionCount : null};
}

export function summarizeConfirmation(rows) {
  const summary = {};
  for (const count of [3, 4, 5]) {
    const cases = rows.filter(r => r.block.count === count);
    if (!cases.length) continue;
    const arms = Object.fromEntries(ARMS.map(arm => [arm, {
      focal: playerSummary(cases, arm, 'focal'), responder: playerSummary(cases, arm, 'responder'),
      meanAcceptedTrades: mean(cases.map(r => r.arms[arm].trades.accepted))
    }]));
    const effects = Object.fromEntries(Object.entries(EFFECTS).map(([name, [left, right, role]]) => {
      const delta = r => {
        const s = role === 'focal' ? r.block.seat : r.block.responderSeat;
        return r.arms[left].players[s].winCredit - r.arms[right].players[s].winCredit;
      };
      return [name, pairedInterval(cases.map(delta))];
    }));
    const groups = {seat: b => b.seat, faction: b => b.faction, mode: b => b.mode};
    const descriptive = Object.fromEntries(Object.entries(groups).map(([name, key]) => [name,
      Object.fromEntries([...new Set(cases.map(r => key(r.block)))].map(value => [value,
        Object.fromEntries(ARMS.map(arm => [arm,
          playerSummary(cases.filter(r => key(r.block) === value), arm, 'focal')]))]))]));
    summary[count] = {blocks: cases.length, arms, effects, descriptive};
  }
  return summary;
}

export async function runStudy({backend, smoke = false} = {}) {
  if (!['weighted', 'greedy'].includes(backend)) throw new TypeError('Select weighted or greedy.');
  if (execFileSync('git', ['status', '--porcelain', '--', '.'], {encoding: 'utf8'}).trim())
    throw new Error('Study requires clean committed source.');
  await verifyRelease(process.cwd());
  const bytes = await Promise.all(INPUTS.map(name => readFile(`dist/runtime/${name}.json`)));
  const input = Object.fromEntries(INPUTS.map((name, i) => [name, JSON.parse(bytes[i])]));
  const profiles = input['player-strategies'].profiles;
  const identityOptions = {rulesVariant: canonicalRulesVariant(input['game-config']), profiles,
    backends: [backend], policyProjection: 'batch', experimentKind: 'capacity_counterplay',
    experimentConfiguration: {root: ROOT, smoke, arms: ARMS}};
  const identity = await loadGameIdentity(identityOptions);
  if (identity.provenance.sourceDirty !== false) throw new Error('Dirty identity.');
  const studyHashes = Object.fromEntries(await Promise.all(STUDY_FILES.map(async f =>
    [f, sha256(await readFile(`evidence/studies/${f}`))])));
  const raw = {evidenceType: 'simulation', generatedAt: new Date().toISOString(), root: ROOT,
    backend, smoke, identity, studyHashes, inputHashes: Object.fromEntries(INPUTS.map((n, i) => [n, sha256(bytes[i])])),
    training: [], confirmation: [], games: 0, parityControls: 0};
  const suffix = `${backend}${smoke ? '-smoke' : ''}`;
  const base = `evidence/studies/simulation/2026-10-11-capacity-counterplay-${suffix}`;
  await mkdir('evidence/studies/simulation', {recursive: true});
  const output = `${base}-raw.json`;
  // Reserve the name before execution; a failed attempt is never overwritten.
  await writeFile(output, JSON.stringify({status: 'running', identity}) + '\n', {flag: 'wx'});
  const capacity = profiles.find(p => p.id === 'power_broker');
  const rivals = profiles.filter(p => p.id !== capacity.id);
  async function play(block, roster) {
    let result;
    try { result = await playBlock(input, block, roster); }
    catch (error) {
      raw.failedGame = {block, roster};
      throw error;
    }
    raw.games++;
    if (raw.games % 192 === 0) process.stderr.write(`${suffix} ${block.stage}: ${raw.games} games complete\n`);
    return result;
  }
  const blocks = (stage, count, reps) => smoke
    ? makeBlocks(`smoke-${stage}`, count, backend, 1).slice(0, 2)
    : makeBlocks(stage, count, backend, reps);
  async function select(parent, stage, role, makeRoster) {
    const candidates = candidatesFor(parent, stage, backend);
    const evaluations = [];
    const search = {stage, role, parentId: parent.id, selectedIndex: null, evaluations};
    raw.training.push(search);
    for (const [index, candidate] of candidates.entries()) {
      const outcomes = [];
      const evaluation = {index, profile: candidate, strategyHash: fingerprintObject(candidate.strategy), outcomes};
      evaluations.push(evaluation);
      for (const block of blocks(stage, 4, 1)) {
        const result = await play(block, makeRoster(block, candidate));
        outcomes.push({block, result});
      }
      const results = outcomes.map(({block, result}) => result.players[role === 'focal' ? block.seat : block.responderSeat]);
      Object.assign(evaluation, {winCredit: mean(results.map(p => p.winCredit)), meanScore: mean(results.map(p => p.score))});
    }
    evaluations.sort((a, b) => b.winCredit - a.winCredit || b.meanScore - a.meanScore || a.index - b.index);
    search.selectedIndex = evaluations[0].index;
    return evaluations[0];
  }
  try {
    if (smoke) for (const count of [3, 4, 5]) {
      const block = makeBlocks('projection-control', count, backend, 1)[0];
      const roster = rosterFor(block, capacity, rivals);
      const batch = await playBlock(input, block, roster);
      const rich = await playBlock(input, block, roster, 'rich');
      if (!isDeepStrictEqual(batch, rich)) throw new Error('Rich/batch outcome disagreement.');
      raw.parityControls += 2;
    }
    const generalists = [];
    for (const parent of profiles) generalists.push(await select(parent, `general-${parent.id}`, 'focal',
      (b, p) => rosterFor(b, p, profiles.filter(r => r.id !== parent.id))));
    const champion = generalists.find(e => e.profile.id === capacity.id).profile;
    const field = generalists.filter(e => e.profile.id !== capacity.id);
    const responderParent = [...field].sort((a, b) => b.winCredit - a.winCredit || b.meanScore - a.meanScore || a.profile.id.localeCompare(b.profile.id))[0].profile;
    const trainedRivals = field.map(e => e.profile);
    const response = (await select(responderParent, 'response', 'responder',
      (b, p) => rosterFor(b, champion, trainedRivals, p))).profile;
    const adapted = (await select(champion, 'adaptation', 'focal',
      (b, p) => rosterFor(b, p, trainedRivals, response))).profile;
    const selection = {champion, responderParent, response, adapted, trainedRivals};
    const frozenSelection = JSON.stringify({identity, studyHashes, selection,
      strategyHashes: Object.fromEntries(Object.entries({champion, responderParent, response, adapted})
        .map(([k, p]) => [k, fingerprintObject(p.strategy)]))}, null, 2) + '\n';
    await writeFile(`${base}-selection.json`, frozenSelection, {flag: 'wx'});
    raw.selection = selection;
    raw.selectionHash = sha256(frozenSelection);
    process.stderr.write(`${suffix}: selection frozen before confirmation (${raw.selectionHash})\n`);
    for (const count of [3, 4, 5]) for (const block of blocks('confirmation', count, count === 4 ? 16 : 4)) {
      const rosters = {
        authored: rosterFor(block, capacity, rivals, rivals.find(p => p.id === responderParent.id)),
        field: rosterFor(block, capacity, trainedRivals, responderParent),
        equal_budget: rosterFor(block, champion, trainedRivals, responderParent),
        counter: rosterFor(block, champion, trainedRivals, response),
        adapted: rosterFor(block, adapted, trainedRivals, response),
        mirror: Array(block.count).fill(champion)
      };
      const arms = {};
      raw.confirmation.push({block, rosterIds: Object.fromEntries(ARMS.map(a => [a, rosters[a].map(p => p.id)])), arms});
      for (const arm of ARMS) arms[arm] = await play(block, rosters[arm]);
    }
    const finalIdentity = await loadGameIdentity(identityOptions);
    if (!isDeepStrictEqual(identity, finalIdentity)) throw new Error('Source/input identity changed during study.');
    const finalHashes = await Promise.all(STUDY_FILES.map(f => readFile(`evidence/studies/${f}`).then(sha256)));
    if (STUDY_FILES.some((f, i) => studyHashes[f] !== finalHashes[i])) throw new Error('Study protocol/runner changed.');
    raw.summary = summarizeConfirmation(raw.confirmation);
    const primary = raw.summary[4].effects;
    raw.gates = {individuallyUsefulCounter: primary.counterOwnGain.lower > 0.04 && primary.capacitySuppression.lower > 0.04,
      adaptiveRecovery: primary.adaptiveRecovery.lower > 0.04};
    raw.status = smoke ? 'smoke_only' : 'complete';
  } catch (error) {
    raw.status = 'failed'; raw.error = {message: error.message, stack: error.stack};
    throw error;
  } finally {
    await writeFile(output, JSON.stringify(raw) + '\n');
    process.stderr.write(`${suffix}: retained ${raw.games} games, ${raw.status}, ${output}\n`);
  }
  console.log(JSON.stringify({backend, smoke, games: raw.games, parityControls: raw.parityControls,
    output, sha256: sha256(await readFile(output)), gates: raw.gates,
    summary: Object.fromEntries(Object.entries(raw.summary).map(([count, s]) => [count, {blocks: s.blocks,
      winCredits: Object.fromEntries(ARMS.map(a => [a, s.arms[a].focal.winCredit])), effects: s.effects}]))}));
  return raw;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const backendIndex = process.argv.indexOf('--backend');
  await runStudy({backend: process.argv[backendIndex + 1], smoke: process.argv.includes('--smoke')});
}

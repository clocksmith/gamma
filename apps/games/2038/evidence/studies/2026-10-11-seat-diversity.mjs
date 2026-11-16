import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {isDeepStrictEqual} from 'node:util';
import {SelectedRulesMatch} from '../../lab/environment/selected-rules-match.js';
import {canonicalRulesVariant} from '../../lab/environment/rules-variant.js';
import {createPlayerPolicy} from '../../lab/policies/policy-factory.js';
import {classifyWinningPath} from '../../lab/balance/winning-path.js';
import {createRng, shuffle} from '../../web/src/engine.js';
import {loadGameIdentity, sha256, fingerprintObject} from '../../lab/versioning/game-identity.js';
import {verifyRelease} from '../../tasks/release-artifacts.mjs';
import {makeBlocks, assertOutcome} from './2026-10-11-capacity-counterplay.mjs';

export const ROOT = 'seat-diversity-128-20261011-v1';
const INPUTS = ['game-config', 'factions', 'headlines', 'projects', 'mandates'];
const FILES = ['2026-10-11-seat-diversity.mjs', '2026-10-11-seat-diversity-preregistration.md'];
const SELECTION_HASHES = {greedy: 'bc71ae724ddb1fdc529196ace9e4a1667e651c6f9648d25b28347bebbbd19429',
  weighted: '016fe50544dc8528cee15f578937a4c0193165849ce5ce27b5b49b82e1fc87ae'};
const ACTIONS = ['fund', 'research', 'build', 'organize', 'deploy', 'influence'];
const mean = xs => xs.reduce((s, x) => s + x, 0) / xs.length;
const rotate = (xs, offset) => xs.map((_, i) => xs[(i + offset) % xs.length]);
const basePath = (backend, phase, smoke) =>
  `evidence/studies/simulation/2026-10-11-seat-diversity-${backend}-${phase}${smoke ? '-smoke' : ''}`;

export function subsets(xs, n) {
  if (n === 0) return [[]];
  return xs.flatMap((x, i) => subsets(xs.slice(i + 1), n - 1).map(rest => [x, ...rest]));
}

export function seatBlocks(backend, count, smoke = false) {
  const groups = subsets([0, 1, 2, 3, 4, 5], count), rows = [];
  for (const [subset, ids] of groups.entries()) for (const mode of ['variable', 'fixed'])
    for (let repeat = 0; repeat < {3: 15, 4: 20, 5: 50}[count]; repeat++) {
      const seed = `${ROOT}:${smoke ? 'smoke-seat' : 'seat'}:${backend}:${count}:${subset}:${mode}:${repeat}`;
      const order = shuffle(ids, createRng(`${seed}:institutions`));
      rows.push({seed, count, subset, mode, repeat, institutions: order,
        rotations: order.map((_, r) => rotate(order, r))});
      if (smoke) return rows;
    }
  return rows;
}

export function leagueBlocks(backend, smoke = false) {
  const rows = [];
  for (const [subset, ids] of subsets([0, 1, 2, 3, 4, 5], 4).entries())
    for (const mode of ['variable', 'fixed']) for (let repeat = 0; repeat < 2; repeat++) {
      const setup = `${ROOT}:${smoke ? 'smoke-league' : 'league'}:${backend}:${subset}:${mode}:${repeat}`;
      const institutions = shuffle(ids, createRng(`${setup}:institutions`));
      for (let policyRotation = 0; policyRotation < 4; policyRotation++)
        for (let factionRotation = 0; factionRotation < 4; factionRotation++)
          rows.push({seed: `${setup}:${policyRotation}:${factionRotation}`, count: 4, subset, mode, repeat,
            policyRotation, factionRotation, institutions: rotate(institutions, factionRotation)});
      if (smoke) return rows;
    }
  return rows;
}

// Theorem 11, Maurer/Pontil: range-scaled, two-sided union over a frozen family.
export function boundedInterval(xs, family) {
  if (!['seat', 'policy'].includes(family) || xs.length < 2 ||
      xs.some(x => !Number.isFinite(x) || x < -1 || x > 1))
    throw new RangeError('Use a registered family and at least two bounded observations.');
  const n = xs.length, estimate = mean(xs);
  const variance = xs.reduce((s, x) => s + (x - estimate) ** 2, 0) / (n - 1);
  const comparisons = family === 'seat' ? 38 : 12, alpha = 0.025;
  const log = Math.log(4 * comparisons / alpha);
  const radius = Math.sqrt(2 * variance * log / n) + 14 * log / (3 * (n - 1));
  return {n, mean: estimate, variance, radius, lower: Math.max(-1, estimate - radius),
    upper: Math.min(1, estimate + radius), comparisons, alpha,
    method: 'fixed-look empirical Bernstein; independent observations; two-sided Bonferroni'};
}

export async function playGame(input, block, roster, backend, projection = 'batch') {
  const policies = roster.map(p => createPlayerPolicy(p, backend, {rosterProfileIds: roster.map(p => p.id)}));
  const match = new SelectedRulesMatch({config: input['game-config'],
    factions: block.institutions.map(i => input.factions.factions[i]), profiles: roster,
    backends: roster.map(() => backend), headlines: input.headlines, projects: input.projects,
    mandates: input.mandates, seed: block.seed, playerCount: block.count,
    mandateMode: block.mode, projection, recordReplay: false});
  const result = await match.play(policies);
  assertOutcome(match, result);
  const players = [...result.standings].sort((a, b) => a.seat - b.seat).map(p => {
    const scoreParts = {capability: p.capability * input['game-config'].scoring.capability,
      customers: p.customers * match.rulesVariant.customerPoints,
      reputation: p.reputation * input['game-config'].scoring.reputation,
      agi: p.agiDeclared ? input['game-config'].scoring.agi : 0,
      objectives: Object.values(p.metrics.mandatesWon).reduce((s, x) => s + x, 0)};
    if (Object.values(scoreParts).reduce((s, x) => s + x, 0) !== p.score) throw new Error('Score does not reconcile.');
    return {seat: p.seat, factionId: p.factionId, profileId: p.profileId, score: p.score, scoreParts,
      winCredit: result.winnerSeats.includes(p.seat) ? 1 / result.winnerSeats.length : 0,
      actions: p.metrics.actions, opening: p.metrics.openingActions,
      holdings: Object.fromEntries(['runway', 'compute', 'capability', 'reputation', 'customers'].map(k => [k, p[k]])),
      winningPath: classifyWinningPath(p), agiDeclared: p.agiDeclared,
      forcedNoOps: p.metrics.forcedNoOps, policyFallbacks: p.metrics.policyFallbacks};
  });
  return {winnerSeats: result.winnerSeats, players, trades: result.matchMetrics.trades};
}

export function summarizeSeats(rows) {
  return Object.fromEntries([3, 4, 5].map(count => {
    const rs = rows.filter(r => r.block.count === count);
    const seatRates = Array.from({length: count}, (_, s) => mean(rs.map(r =>
      mean(r.games.map(g => g.players[s].winCredit)))));
    const effects = [];
    if (rs.length > 1) for (let a = 0; a < count; a++) for (let b = a + 1; b < count; b++)
      effects.push({left: a, right: b, ...boundedInterval(rs.map(r =>
        mean(r.games.map(g => g.players[a].winCredit - g.players[b].winCredit))), 'seat')});
    const players = rs.flatMap(r => r.games.flatMap(g => g.players));
    return [count, {blocks: rs.length, games: rs.reduce((s, r) => s + r.games.length, 0), seatRates,
      observedRange: Math.max(...seatRates) - Math.min(...seatRates), effects,
      equivalence: effects.length > 0 && effects.every(e => e.lower >= -0.10 && e.upper <= 0.10),
      materialExcess: effects.some(e => e.lower > 0.10 || e.upper < -0.10),
      nonzero: effects.filter(e => e.lower > 0 || e.upper < 0),
      noOpRate: players.reduce((s, p) => s + p.forcedNoOps, 0) / (players.length * 12)}];
  }));
}

function distribution(counts) {
  const total = Object.values(counts).reduce((s, x) => s + x, 0), positive = Object.values(counts).filter(x => x > 0);
  return {counts, observed: positive.length, entropy: positive.length < 2 ? 0 :
    -positive.reduce((s, x) => s + x / total * Math.log(x / total), 0) / Math.log(positive.length),
    topShare: total ? Math.max(...positive) / total : 0};
}

export function comparableSets(ids, pairs) {
  const sets = [];
  for (let mask = 1; mask < 2 ** ids.length; mask++) {
    const set = ids.filter((_, i) => mask & 2 ** i);
    if (set.length < 2) continue;
    if (set.every((a, i) => set.slice(i + 1).every(b => pairs.some(e =>
      ((e.left === a && e.right === b) || (e.left === b && e.right === a)) && e.comparable)))) sets.push(set);
  }
  return sets.filter(s => !sets.some(t => t.length > s.length && s.every(x => t.includes(x))));
}

export function summarizeLeague(rows, profiles) {
  const totals = {}, paths = {}, actions = {}, openings = {};
  const add = (map, k, n = 1) => { map[k] = (map[k] || 0) + n; };
  for (const g of rows.map(r => r.result)) for (const p of g.players) {
    totals[p.profileId] ||= []; totals[p.profileId].push(p);
    actions[p.profileId] ||= {}; openings[p.profileId] ||= {}; paths[p.profileId] ||= {};
    for (const [k, n] of Object.entries(p.actions)) add(actions[p.profileId], k, n);
    for (const [k, n] of Object.entries(p.actions)) add(actions, k, n);
    add(openings[p.profileId], p.opening.join(' → ')); add(openings, p.opening.join(' → '));
    add(paths[p.profileId], p.winningPath, p.winCredit); add(paths, p.winningPath, p.winCredit);
  }
  const ids = profiles.map(p => p.id), effects = [];
  const policyStats = Object.fromEntries(ids.map(id => [id, {n: totals[id].length,
    winCredit: mean(totals[id].map(p => p.winCredit)), score: mean(totals[id].map(p => p.score)),
    scoreParts: Object.fromEntries(Object.keys(totals[id][0].scoreParts).map(k => [k, mean(totals[id].map(p => p.scoreParts[k]))])),
    actions: distribution(actions[id]), openings: distribution(openings[id]), paths: distribution(paths[id])}]));
  for (const [i, left] of ids.entries()) for (const right of ids.slice(i + 1)) {
    const e = boundedInterval(rows.map(r => r.result.players.find(p => p.profileId === left).winCredit -
      r.result.players.find(p => p.profileId === right).winCredit), 'policy');
    const norm = id => ACTIONS.map(a => (actions[id][a] || 0) /
      Object.values(actions[id]).reduce((s, n) => s + n, 0));
    const x = norm(left), y = norm(right);
    effects.push({left, right, ...e, comparable: e.lower >= -0.18 && e.upper <= 0.18,
      actionMixDistance: x.reduce((s, n, j) => s + Math.abs(n - y[j]), 0) / 2});
  }
  const aggregate = map => distribution(Object.fromEntries(Object.entries(map).filter(([, v]) => typeof v === 'number')));
  const players = rows.flatMap(r => r.result.players);
  return {games: rows.length, policies: policyStats, effects, comparableSets: comparableSets(ids, effects),
    allPolicies: {actions: aggregate(actions), openings: aggregate(openings), paths: aggregate(paths)},
    noOpRate: players.reduce((s, p) => s + p.forcedNoOps, 0) / (players.length * 12)};
}

export async function runStudy({backend, phase, smoke = false}) {
  if (!Object.hasOwn(SELECTION_HASHES, backend) || !['seat', 'diversity'].includes(phase)) throw new TypeError('Choose backend and phase.');
  if (execFileSync('git', ['status', '--porcelain'], {encoding: 'utf8'}).trim()) throw new Error('Clean source required.');
  await verifyRelease(process.cwd());
  const inputBytes = await Promise.all(INPUTS.map(n => readFile(`dist/runtime/${n}.json`)));
  const input = Object.fromEntries(INPUTS.map((n, i) => [n, JSON.parse(inputBytes[i])]));
  const selectionBytes = await readFile(`evidence/studies/simulation/2026-10-11-capacity-counterplay-${backend}-selection.json`);
  if (sha256(selectionBytes) !== SELECTION_HASHES[backend]) throw new Error('Frozen selection changed.');
  const frozen = JSON.parse(selectionBytes), selection = frozen.selection;
  const profiles = [selection.champion, ...selection.trainedRivals];
  const options = {rulesVariant: canonicalRulesVariant(input['game-config']), profiles, backends: [backend],
    policyProjection: 'batch', experimentKind: 'seat_diversity', experimentConfiguration: {root: ROOT, phase, smoke}};
  const identity = await loadGameIdentity(options);
  if (identity.provenance.sourceDirty !== false || !isDeepStrictEqual(identity.game, frozen.identity.game) ||
      !isDeepStrictEqual(identity.engine, frozen.identity.engine)) throw new Error('Launch game/engine identity differs.');
  const hashes = Object.fromEntries(await Promise.all(FILES.map(async f => [f, sha256(await readFile(`evidence/studies/${f}`))])));
  const raw = {evidenceType: 'simulation', root: ROOT, backend, phase, smoke, generatedAt: new Date().toISOString(),
    identity, fileHashes: hashes, selectionHash: sha256(selectionBytes),
    inputHashes: Object.fromEntries(INPUTS.map((n, i) => [n, sha256(inputBytes[i])])),
    games: 0, seats: [], screening: [], league: [], status: 'running'};
  if (phase === 'diversity') {
    raw.seatPrerequisites = {};
    for (const b of ['greedy', 'weighted']) {
      const bytes = await readFile(`${basePath(b, 'seat', false)}-raw.json`), prior = JSON.parse(bytes);
      if (prior.status !== 'complete' || !isDeepStrictEqual(prior.fileHashes, hashes) ||
          !isDeepStrictEqual(prior.identity.game, identity.game) || !isDeepStrictEqual(prior.identity.engine, identity.engine))
        throw new Error('Both full seat controls must finish under this protocol and game first.');
      raw.seatPrerequisites[b] = {sha256: sha256(bytes), sourceCommit: prior.identity.provenance.sourceCommit};
    }
  }
  const output = `${basePath(backend, phase, smoke)}-raw.json`;
  await mkdir('evidence/studies/simulation', {recursive: true});
  await writeFile(output, JSON.stringify({status: 'running', identity}) + '\n', {flag: 'wx'});
  async function play(block, roster, projection = 'batch') {
    raw.activeGame = {block, rosterIds: roster.map(p => p.id), projection};
    const result = await playGame(input, block, roster, backend, projection);
    raw.games++;
    if (raw.games % 240 === 0) process.stderr.write(`${backend} ${phase}: ${raw.games} games complete\n`);
    return result;
  }
  try {
    if (phase === 'seat') {
      for (const count of [3, 4, 5]) for (const block of seatBlocks(backend, count, smoke)) {
        const row = {block, games: []}; raw.seats.push(row);
        for (const institutions of block.rotations) {
          const b = {...block, institutions}, roster = Array(count).fill(selection.champion);
          const result = await play(b, roster); row.games.push(result);
          if (smoke && !isDeepStrictEqual(result, await play(b, roster, 'rich'))) throw new Error('Rich/batch disagreement.');
        }
      }
      raw.summary = summarizeSeats(raw.seats);
    } else {
      const blocks = makeBlocks(smoke ? 'smoke-screening' : 'screening', 4, backend, 2).map(b => ({...b,
        seed: b.seed.replace('capacity-counterplay-128-20261011-v1', ROOT),
        institutions: Array.from({length: 4}, (_, s) => (b.faction + s - b.seat + 6) % 6)}));
      for (const profile of profiles) {
        const row = {profile, strategyHash: fingerprintObject(profile.strategy), outcomes: []}; raw.screening.push(row);
        for (const block of (smoke ? blocks.slice(0, 2) : blocks)) {
          const roster = Array(4).fill(selection.champion); roster[block.seat] = profile;
          row.outcomes.push({block, result: await play(block, roster)});
        }
        const ps = row.outcomes.map(r => r.result.players[r.block.seat]);
        row.winCredit = mean(ps.map(p => p.winCredit)); row.meanScore = mean(ps.map(p => p.score));
      }
      const ranked = [...raw.screening].sort((a, b) => b.winCredit - a.winCredit || b.meanScore - a.meanScore || a.profile.id.localeCompare(b.profile.id));
      const selected = ranked.slice(0, 4).map(r => r.profile);
      const artifact = JSON.stringify({identity, fileHashes: hashes, screening: ranked.map(r => ({id: r.profile.id,
        winCredit: r.winCredit, meanScore: r.meanScore, strategyHash: r.strategyHash})), selected}, null, 2) + '\n';
      await writeFile(`${basePath(backend, phase, smoke)}-selection.json`, artifact, {flag: 'wx'});
      raw.selected = selected; raw.leagueSelectionHash = sha256(artifact);
      process.stderr.write(`${backend}: strongest four frozen before held-out league (${raw.leagueSelectionHash})\n`);
      for (const block of leagueBlocks(backend, smoke)) raw.league.push({block,
        result: await play(block, rotate(selected, block.policyRotation))});
      raw.summary = summarizeLeague(raw.league, selected);
    }
    if (!isDeepStrictEqual(identity, await loadGameIdentity(options))) throw new Error('Identity drift.');
    for (const f of FILES) if (sha256(await readFile(`evidence/studies/${f}`)) !== hashes[f]) throw new Error('Protocol drift.');
    if (sha256(await readFile(`evidence/studies/simulation/2026-10-11-capacity-counterplay-${backend}-selection.json`)) !== raw.selectionHash)
      throw new Error('Frozen selection drift.');
    if (phase === 'diversity' && sha256(await readFile(`${basePath(backend, phase, smoke)}-selection.json`)) !== raw.leagueSelectionHash)
      throw new Error('League selection drift.');
    delete raw.activeGame;
    raw.status = smoke ? 'smoke_only' : 'complete';
  } catch (e) {raw.status = 'failed'; raw.error = {message: e.message, stack: e.stack}; throw e;}
  finally {await writeFile(output, JSON.stringify(raw) + '\n'); process.stderr.write(`${backend} ${phase}: retained ${raw.games}, ${raw.status}, ${output}\n`);}
  console.log(JSON.stringify({backend, phase, smoke, games: raw.games, output,
    sha256: sha256(await readFile(output)), summary: raw.summary}));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const value = key => process.argv[process.argv.indexOf(key) + 1];
  await runStudy({backend: value('--backend'), phase: value('--phase'), smoke: process.argv.includes('--smoke')});
}

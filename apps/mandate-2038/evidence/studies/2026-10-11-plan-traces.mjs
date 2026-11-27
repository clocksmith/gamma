import {readFile, writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {isDeepStrictEqual} from 'node:util';
import {pathToFileURL} from 'node:url';
import {SelectedRulesMatch} from '../../lab/environment/selected-rules-match.js';
import {createPlayerPolicy} from '../../lab/policies/policy-factory.js';
import {classifyWinningPath} from '../../lab/balance/winning-path.js';
import {loadGameIdentity, sha256} from '../../lab/versioning/game-identity.js';
import {canonicalRulesVariant} from '../../lab/environment/rules-variant.js';
import {verifyRelease} from '../../tasks/release-artifacts.mjs';
import {assertOutcome} from './2026-10-11-capacity-counterplay.mjs';
import {observeMatch} from './2026-10-11-reputation-counter.mjs';

const INPUTS = ['game-config', 'factions', 'headlines', 'projects', 'mandates'];
const FILES = ['2026-10-11-plan-traces.mjs', '2026-10-11-plan-traces-protocol.md'];
const SOURCE_HASHES = {
  greedy: '4742a7d1ef25964cf42c3c89348722cb9701b7dd022e6f50dfb1248a6364e976',
  weighted: 'e14f2f9a89ee219b9607c4353aed5dcce9c33e79dc9016328c13d8292acd3add'
};
const holdings = p => Object.fromEntries(['runway', 'compute', 'capability', 'reputation', 'customers'].map(k => [k, p[k]]));
const rotate = (xs, offset) => xs.map((_, i) => xs[(i + offset) % xs.length]);

export function selectTraces(league, profiles, factions) {
  const selected = new Map(), missing = [];
  for (const profile of profiles) for (const faction of factions) for (const mode of ['fixed', 'variable']) {
    const cell = {profileId: profile.id, factionId: faction.id, mode};
    const eligible = league.map((row, index) => ({row, index, hash: sha256(row.block.seed)}))
      .filter(({row}) => row.block.mode === mode && row.result.players.some(p =>
        p.profileId === profile.id && p.factionId === faction.id && p.winCredit > 0))
      .sort((a, b) => a.hash.localeCompare(b.hash) || a.index - b.index);
    if (!eligible.length) {missing.push(cell); continue;}
    const {row, index} = eligible[0];
    if (!selected.has(index)) selected.set(index, {index, row, cells: []});
    selected.get(index).cells.push(cell);
  }
  return {games: [...selected.values()].sort((a, b) => a.index - b.index), missing};
}

export function summarizeOutcome(result, config) {
  return {winnerSeats: result.winnerSeats,
    players: [...result.standings].sort((a, b) => a.seat - b.seat).map(p => ({
      seat: p.seat, factionId: p.factionId, profileId: p.profileId, score: p.score,
      scoreParts: {capability: p.capability * config.scoring.capability,
        customers: p.customers * result.rulesVariant.customerPoints,
        reputation: p.reputation * config.scoring.reputation,
        agi: p.agiDeclared ? config.scoring.agi : 0,
        objectives: Object.values(p.metrics.mandatesWon).reduce((s, x) => s + x, 0)},
      winCredit: result.winnerSeats.includes(p.seat) ? 1 / result.winnerSeats.length : 0,
      actions: p.metrics.actions, opening: p.metrics.openingActions, holdings: holdings(p),
      winningPath: classifyWinningPath(p), agiDeclared: p.agiDeclared,
      forcedNoOps: p.metrics.forcedNoOps, policyFallbacks: p.metrics.policyFallbacks
    })), trades: result.matchMetrics.trades};
}

export async function captureGame(input, block, roster, backend) {
  const match = new SelectedRulesMatch({config: input['game-config'],
    factions: block.institutions.map(i => input.factions.factions[i]), profiles: roster,
    backends: roster.map(() => backend), headlines: input.headlines, projects: input.projects,
    mandates: input.mandates, seed: block.seed, playerCount: block.count,
    mandateMode: block.mode, projection: 'batch', recordReplay: true});
  const initialState = match.snapshot(), observed = observeMatch(match), decisions = [];
  const research = match.research.bind(match);
  match.research = async (policies, seat, decision) => {
    const before = holdings(match.players[seat]);
    await research(policies, seat, decision);
    observed.resolutions.push({round: match.round, cycle: match.cycle, seat,
      action: 'research', parameters: structuredClone(decision.parameters), before,
      after: holdings(match.players[seat]), research: structuredClone(match.players[seat].metrics.researchCapability.at(-1))});
  };
  const policies = roster.map(profile => {
    const parent = createPlayerPolicy(profile, backend, {rosterProfileIds: roster.map(p => p.id)});
    return {async decide(packet) {
      const stage = packet.requestId.split(':').at(-2);
      const row = {requestId: packet.requestId, round: packet.round, cycle: packet.cycle,
        seat: packet.seat, profileId: profile.id, stage,
        observation: structuredClone(packet.observation), legalDecisions: structuredClone(packet.legalDecisions)};
      if (stage === 'select') row.resolutions = Object.fromEntries(packet.legalDecisions.map(d =>
        [d.actionId, structuredClone(match.legalResolutions(packet.seat, d.actionId))]));
      const response = await parent.decide(packet);
      row.response = structuredClone(response);
      row.weights = parent.rank(packet).map(r => ({decisionId: r.decision.decisionId, weight: r.weight}));
      decisions.push(row);
      return response;
    }};
  });
  const result = await match.play(policies);
  assertOutcome(match, result);
  const outcome = summarizeOutcome(result, input['game-config']);
  if (decisions.filter(d => d.stage === 'select').length !== block.count * 12)
    throw new Error('Trace omitted an action selection.');
  if (observed.production.length !== 4 || observed.reviews.length !== 4)
    throw new Error('Trace omitted an Era settlement.');
  return {initialState, decisions, observed, finalState: match.snapshot(), outcome, result};
}

export async function runCapture(backend) {
  if (!Object.hasOwn(SOURCE_HASHES, backend)) throw new TypeError('Choose greedy or weighted.');
  if (execFileSync('git', ['status', '--porcelain'], {encoding: 'utf8'}).trim()) throw new Error('Clean source required.');
  await verifyRelease(process.cwd());
  const sourcePath = `evidence/studies/simulation/2026-10-11-seat-diversity-${backend}-diversity-raw.json`;
  const sourceBytes = await readFile(sourcePath);
  if (sha256(sourceBytes) !== SOURCE_HASHES[backend]) throw new Error('Frozen league changed.');
  const source = JSON.parse(sourceBytes);
  if (source.status !== 'complete') throw new Error('Complete league required.');
  const inputBytes = await Promise.all(INPUTS.map(n => readFile(`dist/runtime/${n}.json`)));
  const input = Object.fromEntries(INPUTS.map((n, i) => [n, JSON.parse(inputBytes[i])]));
  for (const [i, n] of INPUTS.entries()) if (sha256(inputBytes[i]) !== source.inputHashes[n]) throw new Error('Input drift.');
  const options = {rulesVariant: canonicalRulesVariant(input['game-config']), profiles: source.selected,
    backends: [backend], policyProjection: 'batch', experimentKind: 'existing_plan_traces'};
  const identity = await loadGameIdentity(options);
  if (identity.provenance.sourceDirty !== false || !isDeepStrictEqual(identity.game, source.identity.game) ||
      !isDeepStrictEqual(identity.engine, source.identity.engine)) throw new Error('Game or engine drift.');
  const fileHashes = Object.fromEntries(await Promise.all(FILES.map(async f => [f, sha256(await readFile(`evidence/studies/${f}`))])));
  const selected = selectTraces(source.league, source.selected, input.factions.factions);
  const raw = {status: 'running', evidenceType: 'simulation_trace', backend, generatedAt: new Date().toISOString(),
    identity, sourcePath, sourceHash: sha256(sourceBytes), sourceIdentity: source.identity,
    fileHashes, inputHashes: source.inputHashes, missing: selected.missing,
    selection: selected.games.map(({index, cells}) => ({index, cells})), games: []};
  const output = `evidence/studies/simulation/2026-10-11-plan-traces-${backend}-raw.json`;
  await writeFile(output, JSON.stringify({status: 'running', identity}) + '\n', {flag: 'wx'});
  try {
    for (const {index, row, cells} of selected.games) {
      raw.activeGame = {index, seed: row.block.seed};
      const trace = await captureGame(input, row.block, rotate(source.selected, row.block.policyRotation), backend);
      raw.games.push({index, cells, block: row.block, ...trace});
      if (!isDeepStrictEqual(trace.outcome, row.result)) throw new Error(`Archived outcome mismatch at ${index}.`);
      process.stderr.write(`${backend}: ${raw.games.length}/${selected.games.length} complete traces, archive parity\n`);
    }
    if (!isDeepStrictEqual(identity, await loadGameIdentity(options))) throw new Error('Identity drift.');
    if (sha256(await readFile(sourcePath)) !== raw.sourceHash) throw new Error('League drift.');
    for (const f of FILES) if (sha256(await readFile(`evidence/studies/${f}`)) !== fileHashes[f]) throw new Error('Capture source drift.');
    delete raw.activeGame; raw.status = 'complete';
  } catch (error) {raw.status = 'failed'; raw.error = {message: error.message, stack: error.stack}; throw error;}
  finally {await writeFile(output, JSON.stringify(raw) + '\n');}
  console.log(JSON.stringify({backend, status: raw.status, traces: raw.games.length,
    missing: raw.missing, output, sha256: sha256(await readFile(output))}));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href)
  await runCapture(process.argv[process.argv.indexOf('--backend') + 1]);

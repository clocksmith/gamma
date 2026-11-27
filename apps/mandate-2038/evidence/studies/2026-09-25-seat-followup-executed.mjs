import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { createSimulation } from '/Users/xyz/deco/gamma/games/2038/lab/runtime/create-simulation.js';
import { archiveSimulationReport } from '/Users/xyz/deco/gamma/games/2038/lab/report-archive.js';

const root = '/Users/xyz/deco/gamma/games/2038';
const output = resolve(root, 'evidence/studies/simulation/2038-seat-followup-20260925-v1.json');
const factions = JSON.parse(await readFile(resolve(root, 'dist/runtime/factions.json'))).factions.map(x => x.id);
const rivalProfiles = ['balanced_operator', 'capability_rusher', 'market_maximalist'];
const treatments = ['personal_infrastructure_v1', 'research_deploy_plan_v1'];
const seeds = ['seat-followup-a-20260925', 'seat-followup-b-20260925'];
const rotations = [1, 2];
const seats = [0, 3];
const backends = ['greedy', 'weighted'];
const contract = {
  label: 'simulation', source: 'clean committed current executable',
  question: 'Does the personal infrastructure minus Research/Deploy score difference in Seat 4 persist across added seeds and rotated rivals, compared with Seat 1?',
  playerCount: 4, focalFactions: factions, seats, backends, seeds, rotations,
  treatments, rivalProfiles, rulesVariant: {}, mandateMode: 'variable',
  simulateNegotiation: true, sampleReplays: 0,
  note: 'Diagnostic policy comparison, not a balance or project-price qualification.'
};
const sha = bytes => `sha256:${createHash('sha256').update(bytes).digest('hex')}`;
const rows = [];
let expectedIdentity;
for (const seed of seeds) for (const rotation of rotations) {
  for (const faction of factions) for (const seat of seats) for (const backend of backends) {
    const rivals = factions.filter(id => id !== faction);
    const orderedRivals = [...rivals.slice(rotation), ...rivals.slice(0, rotation)].slice(0, 3);
    const orderedProfiles = [...rivalProfiles.slice(rotation), ...rivalProfiles.slice(0, rotation)];
    const factionIds = [...orderedRivals]; factionIds.splice(seat, 0, faction);
    const profileIds = [...orderedProfiles]; profileIds.splice(seat, 0, 'infrastructure_compounder');
    const pairSeed = `${seed}-${rotation}-${faction}-${seat}-${backend}`;
    const pair = { seed, rotation, faction, seat, backend, factionIds, profileIds, games: [] };
    for (const treatment of treatments) {
      const policyTreatments = Array(4).fill(null); policyTreatments[seat] = treatment;
      const options = {
        runs: 1, playerCount: 4, seed: pairSeed, factionIds, profileIds,
        backends: Array(4).fill(backend), policyTreatments,
        rotateFactions: false, rotateProfiles: false, mandateMode: 'variable',
        simulateNegotiation: true, rulesVariant: {}, sampleReplays: 0,
        returnOutcomes: true, projection: 'rich'
      };
      const { report, outcomes } = await createSimulation(options);
      if (report.provenance.sourceDirty) throw new Error('Source became dirty during diagnostic.');
      const identity = JSON.stringify({ game: report.game, engine: report.engine, source: report.provenance.sourceCommit });
      if (expectedIdentity && identity !== expectedIdentity) throw new Error('Identity drift during diagnostic.');
      expectedIdentity = identity;
      const archive = await archiveSimulationReport(report, { projectRoot: root, jobId: `seat-followup-${treatment}` });
      const bytes = await readFile(resolve(root, archive.relativePath));
      const outcome = outcomes[0].outcome;
      const focal = outcome.standings.find(player => player.seat === seat);
      pair.games.push({ treatment, score: focal.score,
        winShare: outcome.winnerSeats.includes(seat) ? 1 / outcome.winnerSeats.length : 0,
        projects: focal.metrics.projects, agiDeclared: focal.agiDeclared,
        report: archive.relativePath, reportSha256: sha(bytes) });
    }
    pair.difference = pair.games[0].score - pair.games[1].score;
    rows.push(pair);
    await writeFile(output, JSON.stringify({ schema: 'mandate2038.seatFollowup.v1', contract, complete: false, identity: JSON.parse(expectedIdentity), rows }, null, 2) + '\n');
    process.stdout.write(`${rows.length}/96 ${faction} seat ${seat + 1} ${backend} seed ${seed} rotation ${rotation} difference ${pair.difference}\n`);
  }
}
await writeFile(output, JSON.stringify({ schema: 'mandate2038.seatFollowup.v1', contract, complete: true, identity: JSON.parse(expectedIdentity), rows }, null, 2) + '\n');
process.stdout.write(`${output}\n`);

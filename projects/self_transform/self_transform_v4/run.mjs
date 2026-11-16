import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { performance } from 'node:perf_hooks';
import { fileURLToPath } from 'node:url';
import { serialize, reconstruct, digest } from '../self_transform_v2/operator.mjs';
import { mean } from '../self_transform_v2/experiment.mjs';
import { initialize } from './initialization.mjs';

const here = new URL('.', import.meta.url);
const protocol = JSON.parse(fs.readFileSync(new URL('protocol.json', here)));
const output = process.argv[2];
if (!output) throw new Error('Provide new local receipt path');
const sources = ['initialization.mjs', 'run.mjs', '../self_transform_v2/operator.mjs',
  '../self_transform_v2/experiment.mjs', '../self_transform_v2/run.mjs',
  '../self_transform_v1/evaluator.mjs', '../self_transform_v1/operator.mjs'];
const sourceHashes = Object.fromEntries(sources.map(name =>
  [name, digest(fs.readFileSync(new URL(name, here), 'utf8'))]));
fs.writeFileSync(`${output}.protocol.json`, JSON.stringify({ protocol, sourceHashes }, null, 2), { flag: 'wx' });
const started = performance.now(), initializations = [], records = [];
function worker(mode, input) {
  const processResult = spawnSync(process.execPath,
    [fileURLToPath(new URL('../self_transform_v2/run.mjs', here)), mode],
    { input: JSON.stringify(input), encoding: 'utf8' });
  if (processResult.status !== 0) throw new Error(processResult.stderr);
  return JSON.parse(processResult.stdout);
}
function score(phi, seed) {
  const artifact = serialize(phi);
  const result = worker('--score', { artifact, seed, count: protocol.holdoutCount,
    steps: protocol.steps });
  if (result.artifact !== artifact) throw new Error('Reconstruction mismatch');
  return result;
}
for (const seed of protocol.replicateSeeds) {
  const trainingStart = performance.now();
  const initialization = initialize(protocol, seed);
  initializations.push({ seed, ...initialization, trainingMs: performance.now() - trainingStart });
  const states = Object.fromEntries(protocol.initializers.map(name => [name,
    Object.fromEntries(protocol.arms.map(arm => [arm,
      reconstruct(serialize(initialization.initial[name].phi))]))]));
  for (let generation = 0; generation < protocol.generations; generation += 1) {
    const proposals = [];
    for (const initializer of protocol.initializers) {
      for (const arm of protocol.arms) {
        const start = performance.now(), parent = states[initializer][arm];
        const result = worker('--propose', { parent: serialize(parent),
          initial: serialize(initialization.initial[initializer].phi), arm,
          metaSeed: seed + protocol.seedOffsets.meta + generation,
          metaCount: protocol.metaCount, steps: protocol.steps,
          probeSeed: seed + protocol.seedOffsets.probe + generation });
        proposals.push({ seed, initializer, generation, arm, parent,
          child: reconstruct(result.artifact), proposalBudget: result.budget,
          proposalMs: performance.now() - start });
      }
    }
    // No holdout information enters any proposal, initializer, or future selection.
    for (const proposal of proposals) {
      const start = performance.now();
      const holdoutSeed = seed + protocol.seedOffsets.holdout + generation;
      const parentScore = score(proposal.parent, holdoutSeed);
      const childScore = score(proposal.child, holdoutSeed);
      records.push({ ...proposal, parentScore, childScore, holdoutSeed,
        parentMean: mean(parentScore.losses), childMean: mean(childScore.losses),
        scoringMs: performance.now() - start });
      states[proposal.initializer][proposal.arm] = proposal.child;
    }
  }
}
const receipt = { protocol, sourceHashes, initializations, records,
  elapsedMs: performance.now() - started, node: process.version };
fs.writeFileSync(output, JSON.stringify(receipt, null, 2), { flag: 'wx' });
console.log(JSON.stringify({ elapsedMs: receipt.elapsedMs,
  initializations: initializations.map(({seed,initial,budgets,trainingMs}) => ({seed,
    selected: Object.fromEntries(Object.entries(initial).map(([k,v]) => [k,
      { candidate:v.candidate,parentLoss:v.parentLoss,childLoss:v.childLoss }])), budgets,trainingMs})),
  results: records.map(({seed,initializer,generation,arm,parentMean,childMean}) =>
    ({seed,initializer,generation,arm,parentMean,childMean})) },null,2));

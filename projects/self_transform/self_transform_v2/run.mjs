import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { performance } from 'node:perf_hooks';
import { fileURLToPath } from 'node:url';
import { random, serialize, reconstruct, digest } from './operator.mjs';
import { counter, evaluate, mean, propose, tasks } from './experiment.mjs';
const here = new URL('.', import.meta.url);
if (process.argv[2] === '--propose') {
  const input = JSON.parse(fs.readFileSync(0, 'utf8'));
  const budget = counter();
  const child = propose(reconstruct(input.parent), reconstruct(input.initial), input.arm,
    tasks(input.metaSeed, input.metaCount), input.steps, input.probeSeed, budget);
  process.stdout.write(JSON.stringify({ artifact: serialize(child), budget }));
} else if (process.argv[2] === '--score') {
  const { artifact, seed, count, steps } = JSON.parse(fs.readFileSync(0, 'utf8'));
  const phi = reconstruct(artifact), budget = counter();
  const losses = evaluate(phi, tasks(seed, count), steps, budget);
  process.stdout.write(JSON.stringify({ artifact: serialize(phi), losses, budget }));
} else {
  const output = process.argv[2];
  if (!output) throw new Error('Provide new local receipt path');
  const protocol = JSON.parse(fs.readFileSync(new URL('protocol.json', here)));
  const sourceHashes = Object.fromEntries(['operator.mjs', 'experiment.mjs', 'run.mjs',
    '../self_transform_v1/evaluator.mjs', '../self_transform_v1/operator.mjs'].map(name =>
    [name, digest(fs.readFileSync(new URL(name, here), 'utf8'))]));
  fs.writeFileSync(`${output}.protocol.json`, JSON.stringify({ protocol, sourceHashes }, null, 2), { flag: 'wx' });
  const started = performance.now(), trainingBudget = counter();
  const rng = random(protocol.initializationSeed);
  const training = tasks(protocol.trainingSeed, protocol.trainCount);
  let best;
  for (let n = 0; n < protocol.initialCandidates; n += 1) {
    const phi = Array.from({ length: 4 }, () => rng() * 2 - 1);
    const loss = mean(evaluate(phi, training, protocol.steps, trainingBudget));
    if (!best || loss < best.loss) best = { phi, loss, candidate: n };
  }
  const initializationMs = performance.now() - started;
  const states = Object.fromEntries(protocol.arms.map(arm => [arm, reconstruct(serialize(best.phi))]));
  const records = [];
  function score(phi, generation) {
    const artifact = serialize(phi);
    const worker = spawnSync(process.execPath, [fileURLToPath(import.meta.url), '--score'], {
      input: JSON.stringify({ artifact, seed: protocol.holdoutSeed + generation,
        count: protocol.holdoutCount, steps: protocol.steps }), encoding: 'utf8',
    });
    if (worker.status !== 0) throw new Error(worker.stderr);
    const result = JSON.parse(worker.stdout);
    if (artifact !== result.artifact) throw new Error('Reconstruction mismatch');
    return result;
  }
  for (let generation = 0; generation < protocol.generations; generation += 1) {
    const proposals = protocol.arms.map(arm => {
      const start = performance.now();
      const parent = states[arm];
      const worker = spawnSync(process.execPath, [fileURLToPath(import.meta.url), '--propose'], {
        input: JSON.stringify({ parent: serialize(parent), initial: serialize(best.phi), arm,
          metaSeed: protocol.metaSeed + generation, metaCount: protocol.metaCount,
          steps: protocol.steps, probeSeed: protocol.probeSeed + generation }), encoding: 'utf8',
      });
      if (worker.status !== 0) throw new Error(worker.stderr);
      const result = JSON.parse(worker.stdout);
      return { arm, parent, child: reconstruct(result.artifact), budget: result.budget,
        proposalMs: performance.now() - start };
    });
    for (const proposal of proposals) {
      const start = performance.now();
      const parentScore = score(proposal.parent, generation);
      const childScore = score(proposal.child, generation);
      records.push({ generation, ...proposal, parentScore, childScore,
        parentMean: mean(parentScore.losses), childMean: mean(childScore.losses),
        evaluationAndSubprocessMs: performance.now() - start });
      states[proposal.arm] = proposal.child;
    }
  }
  const receipt = { protocol, sourceHashes, initialization: { ...best, trainingBudget,
    initializationMs }, records, elapsedMs: performance.now() - started, node: process.version };
  fs.writeFileSync(output, JSON.stringify(receipt, null, 2), { flag: 'wx' });
  console.log(JSON.stringify(records.map(({ generation, arm, parentMean, childMean, budget }) =>
    ({ generation, arm, parentMean, childMean, budget })), null, 2));
}

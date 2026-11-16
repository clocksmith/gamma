import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { performance } from 'node:perf_hooks';
import { digest, random, reconstruct, serialize, transform } from './operator.mjs';
import { counter, evaluate, mean, metaGradient, tasks } from './evaluator.mjs';

const here = new URL('.', import.meta.url);
if (process.argv[2] === '--replay') {
  const request = JSON.parse(fs.readFileSync(0, 'utf8'));
  const phi = reconstruct(request.artifact);
  process.stdout.write(JSON.stringify({ artifact: serialize(phi),
    output: transform(phi, request.theta, request.experience) }));
} else {
  const output = process.argv[2];
  if (!output) throw new Error('Usage: node run.mjs <new local receipt path>');
  const protocol = JSON.parse(fs.readFileSync(new URL('protocol.json', here)));
  const sourceHashes = Object.fromEntries(['operator.mjs', 'evaluator.mjs', 'run.mjs']
    .map(name => [name, digest(fs.readFileSync(new URL(name, here), 'utf8'))]));
  // Refuse reuse and write frozen inputs before any candidate evaluation.
  fs.writeFileSync(`${output}.protocol.json`, JSON.stringify({ protocol, sourceHashes }, null, 2),
    { flag: 'wx' });
  const started = performance.now();
  const initializationBudget = counter();
  const rng = random(protocol.seeds.initialization);
  const train = tasks(protocol.seeds.train, protocol.taskCounts.train);
  let best = null;
  for (let i = 0; i < protocol.initialCandidates; i += 1) {
    const phi = Array.from({ length: 4 }, () => rng() * 2 - 1);
    const loss = mean(evaluate(phi, train, protocol.taskSteps, initializationBudget));
    if (!best || loss < best.loss) best = { phi, loss, candidate: i };
  }
  const initializationMs = performance.now() - started;
  const states = Object.fromEntries(protocol.arms.map(arm => [arm, [...best.phi]]));
  const records = [];
  for (let generation = 0; generation < protocol.generations; generation += 1) {
    const meta = tasks(protocol.seeds.meta + generation * 100, protocol.taskCounts.meta);
    const proposals = [];
    for (const arm of protocol.arms) {
      const start = performance.now();
      const budget = counter();
      const parent = states[arm];
      const gradient = metaGradient(parent, meta, protocol.taskSteps,
        protocol.finiteDifferenceEpsilon, budget);
      const self = transform(parent, parent, { gradient });
      budget.transformCalls += 1;
      let child;
      if (arm === 'self') child = self;
      else if (arm === 'gradient') child = parent.map((v, i) =>
        v - protocol.gradientControlRate * gradient[i]);
      else if (arm === 'random') {
        const draw = random(protocol.seeds.randomControl + generation);
        const direction = parent.map(() => draw() * 2 - 1);
        const norm = Math.hypot(...self.map((v, i) => v - parent[i]));
        const denominator = Math.hypot(...direction);
        child = parent.map((v, i) => v + norm * direction[i] / denominator);
      } else child = [...parent];
      const artifact = serialize(child);
      const experience = { gradient: [0.25, -0.5] };
      const replay = spawnSync(process.execPath, [fileURLToPath(import.meta.url), '--replay'], {
        input: JSON.stringify({ artifact, theta: [0.3, -0.7], experience }), encoding: 'utf8',
      });
      if (replay.status !== 0) throw new Error(replay.stderr);
      const recovered = JSON.parse(replay.stdout);
      if (recovered.artifact !== artifact || JSON.stringify(recovered.output)
          !== JSON.stringify(transform(child, [0.3, -0.7], experience))) {
        throw new Error('Fresh process reconstruction mismatch');
      }
      proposals.push({ arm, parent, child, gradient, artifact, budget,
        adaptationAndReconstructionMs: performance.now() - start });
    }
    // All four children are frozen before held-out population construction/evaluation.
    const holdout = tasks(protocol.seeds.holdout + generation * 100,
      protocol.taskCounts.holdout);
    for (const proposal of proposals) {
      const budget = counter();
      const start = performance.now();
      const parentLosses = evaluate(proposal.parent, holdout, protocol.taskSteps, budget);
      const childLosses = evaluate(proposal.child, holdout, protocol.taskSteps, budget);
      records.push({ generation, ...proposal, parentLosses, childLosses,
        parentMean: mean(parentLosses), childMean: mean(childLosses),
        wins: childLosses.filter((v, i) => v < parentLosses[i]).length,
        losses: childLosses.filter((v, i) => v > parentLosses[i]).length,
        evaluationBudget: budget, evaluationMs: performance.now() - start });
      states[proposal.arm] = proposal.child; // Unconditional, never selected on holdout.
    }
  }
  const receipt = { protocol, sourceHashes, initialization: { ...best,
    budget: initializationBudget, ms: initializationMs }, records,
    elapsedMs: performance.now() - started, node: process.version,
    claim: 'Toy self-application only. External gradient oracle and fixed interpreter required.' };
  fs.writeFileSync(output, JSON.stringify(receipt, null, 2), { flag: 'wx' });
  console.log(JSON.stringify({ initialization: receipt.initialization,
    results: records.map(({ generation, arm, parentMean, childMean, wins, losses }) =>
      ({ generation, arm, parentMean, childMean, wins, losses })), elapsedMs: receipt.elapsedMs }, null, 2));
}

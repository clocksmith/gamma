import fs from 'node:fs';
import { reconstruct, serialize } from '../self_transform_v5/operator.mjs';
import { counter, evaluate, propose, tasks } from './experiment.mjs';
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const budget = counter();
if (process.argv[2] === '--propose') {
  const child = propose(reconstruct(input.parent), reconstruct(input.initial), input.arm,
    tasks(input.metaSeed, input.metaCount), input.steps, input.probeSeed, budget, input.rate);
  process.stdout.write(JSON.stringify({ artifact: serialize(child), budget }));
} else if (process.argv[2] === '--score') {
  const phi = reconstruct(input.artifact);
  const losses = evaluate(phi, tasks(input.seed, input.count), input.steps, budget);
  process.stdout.write(JSON.stringify({ artifact: serialize(phi), losses, budget }));
} else throw new Error('Unknown worker mode');

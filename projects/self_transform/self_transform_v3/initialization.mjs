import { random } from '../self_transform_v2/operator.mjs';
import { counter, evaluate, mean, propose, tasks } from '../self_transform_v2/experiment.mjs';

export function initialize(protocol, seed) {
  const offsets = protocol.seedOffsets;
  const rng = random(seed + offsets.candidate);
  const support = tasks(seed + offsets.trainSupport, protocol.trainSupportCount);
  const query = tasks(seed + offsets.trainQuery, protocol.trainQueryCount);
  const budget = counter(), candidates = [];
  for (let candidate = 0; candidate < protocol.initialCandidates; candidate += 1) {
    const phi = Array.from({ length: 4 }, () => rng() * 2 - 1);
    const child = propose(phi, phi, 'hereditary', support, protocol.steps,
      seed + offsets.trainProbe, budget);
    const parentLoss = mean(evaluate(phi, query, protocol.steps, budget));
    const childLoss = mean(evaluate(child, query, protocol.steps, budget));
    candidates.push({ candidate, phi, child, parentLoss, childLoss });
  }
  const taskOnly = candidates.reduce((best, row) => row.parentLoss < best.parentLoss ? row : best);
  const selfTarget = candidates.reduce((best, row) => row.childLoss < best.childLoss ? row : best);
  return { candidates, budget, initial: { task_only: taskOnly, self_target: selfTarget } };
}

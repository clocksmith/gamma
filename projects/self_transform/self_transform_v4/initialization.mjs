import { random } from '../self_transform_v2/operator.mjs';
import { counter, evaluate, mean, propose, tasks } from '../self_transform_v2/experiment.mjs';

export function initialize(protocol, seed) {
  const offsets = protocol.seedOffsets;
  const rng = random(seed + offsets.candidate);
  const initialPhi = Array.from({ length: 4 }, () => rng() * 2 - 1);
  const mutations = Array.from({ length: protocol.trainingCandidates - 1 }, () =>
    Array.from({ length: 4 }, () => protocol.mutationScale * (rng() * 2 - 1)));
  const support = Array.from({ length: protocol.trainingGenerations }, (_, i) =>
    tasks(seed + offsets.trainSupport + i, protocol.trainSupportCount));
  const query = Array.from({ length: protocol.trainingGenerations }, (_, i) =>
    tasks(seed + offsets.trainQuery + i, protocol.trainQueryCount));
  const trajectories = {}, initial = {}, budgets = {};
  for (const initializer of protocol.initializers) {
    const budget = counter(), candidates = [];
    let best;
    for (let candidate = 0; candidate < protocol.trainingCandidates; candidate += 1) {
      const phi = candidate === 0 ? [...initialPhi]
        : best.phi.map((v, i) => v + mutations[candidate - 1][i]);
      let descendant = [...phi];
      const parentLosses = [], descendantLosses = [];
      for (let generation = 0; generation < protocol.trainingGenerations; generation += 1) {
        parentLosses.push(mean(evaluate(phi, query[generation], protocol.steps, budget)));
        descendant = propose(descendant, phi, 'hereditary', support[generation],
          protocol.steps, seed + offsets.trainProbe + generation, budget);
        descendantLosses.push(mean(evaluate(descendant, query[generation], protocol.steps, budget)));
      }
      const parentLoss = mean(parentLosses), childLoss = mean(descendantLosses);
      const fitness = initializer === 'task_only' ? parentLoss : childLoss;
      const row = { candidate, phi, descendant, parentLosses, descendantLosses,
        parentLoss, childLoss, fitness, accepted: !best || fitness < best.fitness };
      candidates.push(row);
      if (row.accepted) best = row;
    }
    initial[initializer] = best;
    trajectories[initializer] = candidates;
    budgets[initializer] = budget;
  }
  return { initial, trajectories, budgets };
}

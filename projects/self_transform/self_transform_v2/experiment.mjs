import { random, transform, estimate } from './operator.mjs';
import { tasks, lossGradient } from '../self_transform_v1/evaluator.mjs';
export { tasks };
export const mean = xs => xs.reduce((s, x) => s + x, 0) / xs.length;
export const counter = () => ({ scalarLossCalls: 0, transforms: 0, metaObjectiveCalls: 0 });

// The external oracle supplies scalars only. Probe geometry is fixed, not learned.
export function probes(theta, objective, seed, radius = 0.001) {
  const rng = random(seed);
  const directions = Array.from({ length: 4 }, () => theta.map(() => rng() < 0.5 ? -1 : 1));
  return { directions, radius,
    plus: directions.map(d => objective(theta.map((v, i) => v + radius * d[i]))),
    minus: directions.map(d => objective(theta.map((v, i) => v - radius * d[i]))) };
}

export function evaluate(phi, population, steps, budget) {
  return population.map((task, index) => {
    const objective = theta => {
      budget.scalarLossCalls += 1;
      return lossGradient(theta, task).loss;
    };
    let theta = [...task.initial];
    for (let step = 0; step < steps; step += 1) {
      const experience = probes(theta, objective, 900000 + index * 100 + step);
      theta = transform(phi, theta, experience);
      budget.transforms += 1;
    }
    return objective(theta);
  });
}

export function propose(parent, initial, arm, population, steps, seed, budget) {
  const objective = phi => {
    budget.metaObjectiveCalls += 1;
    return mean(evaluate(phi, population, steps, budget));
  };
  const experience = probes(parent, objective, seed);
  const proposer = arm === 'fixed_proposer' ? initial : parent;
  const proposal = transform(proposer, parent, experience);
  budget.transforms += 1;
  if (arm === 'serialization_only') return [...parent];
  if (arm === 'spsa') return parent.map((v, i) => v - 0.1 * estimate(parent, experience)[i]);
  return proposal;
}

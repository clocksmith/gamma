import { random, transform, vector } from './operator.mjs';

// Fixed external evaluator. No candidate code execution or mutable scoring policy.
// Rotated 2D quadratics exercise cross-coordinate curvature; all minima are known.
export function tasks(seed, count) {
  const rng = random(seed);
  return Array.from({ length: count }, () => {
    const angle = rng() * Math.PI;
    const c = Math.cos(angle), s = Math.sin(angle);
    const a = 0.2 + 2.8 * rng(), b = 0.2 + 2.8 * rng();
    return {
      minimum: [rng() * 4 - 2, rng() * 4 - 2],
      initial: [rng() * 4 - 2, rng() * 4 - 2],
      matrix: [a * c * c + b * s * s, (a - b) * c * s,
        a * s * s + b * c * c],
    };
  });
}

export function lossGradient(theta, task) {
  vector(theta, 2);
  const x = theta[0] - task.minimum[0], y = theta[1] - task.minimum[1];
  const [a, b, c] = task.matrix;
  return { loss: 0.5 * (a * x * x + 2 * b * x * y + c * y * y),
    gradient: [a * x + b * y, b * x + c * y] };
}

export function evaluate(phi, population, steps, budget) {
  budget.evaluations += 1;
  return population.map(task => {
    let theta = [...task.initial];
    for (let step = 0; step < steps; step += 1) {
      theta = transform(phi, theta, lossGradient(theta, task));
      budget.taskGradientCalls += 1;
      budget.transformCalls += 1;
    }
    budget.lossCalls += 1;
    return lossGradient(theta, task).loss;
  });
}

export const mean = values => values.reduce((a, b) => a + b, 0) / values.length;
export const counter = () => ({ evaluations: 0, taskGradientCalls: 0,
  transformCalls: 0, lossCalls: 0 });

export function metaGradient(phi, population, steps, epsilon, budget) {
  return phi.map((_, i) => {
    const plus = [...phi], minus = [...phi];
    plus[i] += epsilon;
    minus[i] -= epsilon;
    return (mean(evaluate(plus, population, steps, budget))
      - mean(evaluate(minus, population, steps, budget))) / (2 * epsilon);
  });
}

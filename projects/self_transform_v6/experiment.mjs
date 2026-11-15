import { estimate, transform } from '../self_transform_v5/operator.mjs';
import { evaluate, mean, probes, propose as learnedPropose } from '../self_transform_v5/experiment.mjs';
export { counter, evaluate, mean, probes, tasks } from '../self_transform_v5/experiment.mjs';
export function propose(parent, initial, arm, population, steps, seed, budget, rate) {
  if (arm !== 'spsa') return learnedPropose(parent,initial,arm,population,steps,seed,budget);
  if (!Number.isFinite(rate) || rate < 0 || rate > 1) throw new Error('Invalid fixed rate');
  const experience = probes(parent, phi => {
    budget.metaObjectiveCalls += 1;
    return mean(evaluate(phi,population,steps,budget));
  }, seed);
  // Charge identical learned-proposal work, explicitly discarded by this control.
  transform(parent,parent,experience);
  budget.transforms += 1;
  const gradient = estimate(parent,experience);
  return parent.map((v,i)=>v-rate*gradient[i]);
}

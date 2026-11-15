// Clean OS subprocess worker for process-isolated reconstruction, proposal, and held-out scoring.
// Receives ONLY serialized artifacts and deterministic task seeds via stdin; holds zero parent closures.

import fs from 'node:fs';
import {
  counter,
  freezeState,
  reconstruct,
  restoreState,
  serialize,
} from './operator.mjs';
import {
  evaluateRule,
  makeEnvironment,
  proposeSuccessor,
  sampleTasks,
} from './tasks.mjs';

const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const mode = process.argv[2];

if (mode === '--propose') {
  const target = reconstruct(payload.targetArtifact);
  const proposer = reconstruct(payload.proposerArtifact);
  if (target.rule !== proposer.rule) {
    throw new Error('Target and proposer rule mismatch in worker');
  }
  const initialHistory = payload.historyArtifact ? restoreState(payload.historyArtifact) : null;
  const env = makeEnvironment(payload.envSeed);
  const supportTasks = sampleTasks(env, payload.supportSeed, payload.supportCount, payload.family);
  const budget = counter();
  const out = proposeSuccessor({
    targetPhi: target.phi,
    proposerPhi: proposer.phi,
    rule: target.rule,
    arm: payload.arm,
    supportTasks,
    innerSteps: payload.innerSteps,
    metaSteps: payload.metaSteps,
    metaObjectiveId: payload.metaObjectiveId,
    probeBaseSeed: payload.probeBaseSeed,
    innerProbeSeed: payload.innerProbeSeed,
    initialHistory,
    settings: payload.settings ?? {},
  }, budget);

  process.stdout.write(JSON.stringify({
    childArtifact: serialize(out.theta, target.rule),
    historyArtifact: out.history ? freezeState(out.history) : null,
    budget,
    outerBudget: out.outerBudget,
    innerBudget: out.innerBudget,
  }));
} else if (mode === '--score') {
  const { phi, rule } = reconstruct(payload.artifact);
  const env = makeEnvironment(payload.envSeed);
  const tasks = sampleTasks(env, payload.holdoutSeed, payload.holdoutCount, payload.family);
  const budget = counter();
  const losses = evaluateRule(phi, rule, tasks, payload.innerSteps, payload.innerProbeSeed, budget);
  process.stdout.write(JSON.stringify({
    reconstructedArtifact: serialize(phi, rule),
    losses,
    budget,
  }));
} else {
  throw new Error(`Unsupported worker mode: ${mode}`);
}

// Clean OS subprocess worker for process-isolated proposal, weight-free behavioral regeneration, and scoring.
// Receives ONLY serialized artifacts / transcripts and deterministic seeds via stdin; holds zero parent closures.

import fs from 'node:fs';
import { counter } from './observation.mjs';
import {
  freezeState,
  reconstruct,
  regenerateFromTranscript,
  restoreState,
  serialize,
} from './operator.mjs';
import {
  evaluateRule,
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
  const supportTasks = sampleTasks(payload.family, payload.supportSeed, payload.supportCount);
  const budget = counter();
  budget.reconstructionBytes += Buffer.byteLength(payload.targetArtifact) + Buffer.byteLength(payload.proposerArtifact);
  if (payload.historyArtifact) budget.reconstructionBytes += Buffer.byteLength(payload.historyArtifact);

  const emitTranscript = payload.transmission === 'neural_regen';
  const out = proposeSuccessor({
    targetPhi: target.phi,
    proposerPhi: proposer.phi,
    rule: target.rule,
    arm: payload.arm,
    supportTasks,
    innerSteps: payload.innerSteps,
    metaSteps: payload.metaSteps,
    metaObjectiveId: payload.metaObjectiveId,
    initialHistory,
    settings: payload.settings ?? {},
    emitTranscript,
    transcriptProbes: payload.transcriptProbes ?? 24,
    transcriptSeed: payload.transcriptSeed ?? 424242,
  }, budget);

  process.stdout.write(JSON.stringify({
    childArtifact: emitTranscript ? null : serialize(out.theta, target.rule),
    transcript: out.transcript,
    historyArtifact: out.history ? freezeState(out.history) : null,
    budget,
    outerBudget: out.outerBudget,
    innerBudget: out.innerBudget,
  }));
} else if (mode === '--regenerate') {
  // Strictly weight-free channel: rejects any payload containing childArtifact, weightsHex, or phi!
  if ('childArtifact' in payload || 'weightsHex' in payload || 'phi' in payload) {
    throw new Error('Forbidden weight field present in --regenerate subprocess payload');
  }
  const budget = counter();
  const regen = regenerateFromTranscript(payload.transcript, payload.regenSteps ?? 16, budget);
  process.stdout.write(JSON.stringify({
    regeneratedArtifact: serialize(regen.phi, regen.rule),
    initialBehavioralMse: regen.initialBehavioralMse,
    finalBehavioralMse: regen.finalBehavioralMse,
    budget,
  }));
} else if (mode === '--score') {
  const { phi, rule } = reconstruct(payload.artifact);
  const tasks = sampleTasks(payload.family, payload.holdoutSeed, payload.holdoutCount);
  const budget = counter();
  budget.reconstructionBytes += Buffer.byteLength(payload.artifact);
  const losses = evaluateRule(phi, rule, tasks, payload.innerSteps, budget);
  process.stdout.write(JSON.stringify({
    reconstructedArtifact: serialize(phi, rule),
    losses,
    budget,
  }));
} else {
  throw new Error(`Unsupported worker mode: ${mode}`);
}

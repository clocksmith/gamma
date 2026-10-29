import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

import { finalizeWgslWriterV1Diagnostic } from '../../tools/finalize-wgsl-writer-v1-diagnostic.js';

function readJson(filePath) {
  return JSON.parse(readFileSync(filePath, 'utf8'));
}

function sha256File(filePath) {
  return createHash('sha256').update(readFileSync(filePath)).digest('hex');
}

const resultPath = 'docs/status/wgsl-writer-v1-diagnostic-result-2026-07-14.json';
const result = readJson(resultPath);
const replayed = await finalizeWgslWriterV1Diagnostic({
  policyPath: result.policy.path,
  baseCompletionsPath: result.lanes.base.completionReceipt.path,
  baseSemanticPath: result.lanes.base.semanticReceipt.path,
  adapterCompletionsPath: result.lanes.repairAdapter.completionReceipt.path,
  adapterSemanticPath: result.lanes.repairAdapter.semanticReceipt.path,
});

assert.deepEqual(replayed, result);
assert.equal(
  sha256File(resultPath),
  '16fbd260763e9f3704cacc4b547599504dd98d5007d5d41ce1446576b620b94b'
);
assert.equal(result.decision, 'zero_shot_diagnostic_complete');
assert.equal(result.matchedExecution.identicalPrompts, true);
assert.equal(result.matchedExecution.identicalGeneration, true);
assert.equal(result.matchedExecution.submissionsPerCandidate, 1);
assert.equal(result.matchedExecution.retriesPerformed, false);
assert.equal(result.lanes.base.metrics.taskCount, 3);
assert.equal(result.lanes.base.metrics.responseContractPasses, 0);
assert.equal(result.lanes.base.metrics.compilationPasses, 0);
assert.equal(result.lanes.base.metrics.semanticTaskPasses, 0);
assert.equal(result.lanes.base.metrics.maxTokenCapHits, 3);
assert.equal(result.lanes.repairAdapter.metrics.taskCount, 3);
assert.equal(result.lanes.repairAdapter.metrics.responseContractPasses, 0);
assert.equal(result.lanes.repairAdapter.metrics.compilationPasses, 0);
assert.equal(result.lanes.repairAdapter.metrics.semanticTaskPasses, 0);
assert.equal(result.lanes.repairAdapter.metrics.maxTokenCapHits, 0);
assert.equal(result.comparison.transferObserved, false);
assert.equal(result.comparison.anyCompleteWriterBehavior, false);
assert.equal(
  result.comparison.finding,
  'no_complete_shader_behavior_observed_on_visible_mechanics'
);
assert.equal(result.candidateSelected, false);
assert.equal(result.writerCapabilityEstablished, false);
assert.equal(result.confirmationAuthority, false);
assert.equal(result.promotionAuthority, false);
assert.equal(result.productizationAllowed, false);

const baseSemantic = readJson(result.lanes.base.semanticReceipt.path);
const adapterSemantic = readJson(result.lanes.repairAdapter.semanticReceipt.path);
assert.ok(baseSemantic.tasks.every((task) => (
  task.variants[0].compilation.messages.some((message) => (
    message.type === 'error' && message.message.includes('unexpected token')
  ))
)));
assert.ok(adapterSemantic.tasks.every((task) => (
  task.variants[0].compilation.messages.some((message) => (
    message.type === 'error'
      && message.message.includes("cannot use access enumerant 'read' as address space")
  ))
)));

console.log('wgsl-writer-v1-diagnostic-result.test: ok');

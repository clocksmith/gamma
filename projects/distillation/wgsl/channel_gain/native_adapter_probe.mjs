// Bounded integration diagnostic. Its output never enters candidate selection.
import {readFile, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {createNativeRuntime} from './native_runtime.mjs';
import {checkServiceGuard} from './native_smoke.mjs';

const [configPath, protocolPath, promptsPath, outputPath] = process.argv.slice(2);
if (!outputPath) throw new Error('Expected config, protocol, smoke prompts and output paths');
const bytes = await Promise.all([configPath, protocolPath, promptsPath].map(p => readFile(p)));
const config = JSON.parse(bytes[0]);
const original = JSON.parse(bytes[1]);
const row = JSON.parse(bytes[2].toString().trim().split('\n')[0]);
if (row.populationRole !== 'smoke') throw new Error('Adapter probe requires a smoke task');
const protocol = {...original, generation: {...original.generation, maxNewTokens: 4}};
const controller = new AbortController();
const abort = () => controller.abort(new Error('Adapter diagnostic interrupted'));
process.once('SIGTERM', abort);
process.once('SIGINT', abort);
const started = performance.now();
const receipt = {
  schema: 'gamma.channel-gain-adapter-integration-probe/v1',
  createdAt: new Date().toISOString(),
  purpose: 'Verify adapter prefill and decode projection geometry after smoke failure',
  inputSha256: Object.fromEntries(['config', 'protocol', 'smokePrompts'].map((key, i) => [key, createHash('sha256').update(bytes[i]).digest('hex')])),
  taskId: row.taskId,
  generation: protocol.generation,
  overriddenForDiagnosticOnly: ['generation.maxNewTokens'],
  candidateSelection: false,
  shaderChecksEvaluated: false,
  confirmationEvaluated: false,
};
let runtime;
try {
  runtime = await createNativeRuntime(config, protocol, {
    signal: controller.signal,
    guard: () => checkServiceGuard(config),
  });
  receipt.coldModelLoadMs = runtime.coldModelLoadMs;
  receipt.coldAdapterLoadMs = runtime.coldAdapterLoadMs;
  receipt.request = await runtime.generate(runtime.contract(row), {
    adapterEnabled: true,
    id: `${row.taskId}/adapter-integration-probe`,
  });
  receipt.status = 'integration_probe_completed';
} catch (error) {
  receipt.status = 'integration_probe_failed';
  receipt.error = error.stack ?? String(error);
  process.exitCode = 2;
} finally {
  try { await runtime?.close(); } catch (error) {
    receipt.cleanupError = error.stack ?? String(error);
    process.exitCode = 2;
  }
  receipt.totalWallMs = performance.now() - started;
  await writeFile(outputPath, JSON.stringify(receipt, null, 2) + '\n', {flag: 'wx'});
  process.removeListener('SIGTERM', abort);
  process.removeListener('SIGINT', abort);
}
console.log(JSON.stringify({status: receipt.status, tokenCount: receipt.request?.tokenCount, totalWallMs: receipt.totalWallMs, error: receipt.error}));

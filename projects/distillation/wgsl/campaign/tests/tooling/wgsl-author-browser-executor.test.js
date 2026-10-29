import assert from 'node:assert/strict';

import {
  summarizeWgslAuthorBrowserExecution,
} from '../../tools/lib/wgsl-author-browser-executor.js';

const plan = {
  schema: 'doppler.wgsl-author-execution-plan/v1',
  modules: [
    { id: 'compute-module', wgsl: '@compute @workgroup_size(1) fn main() {}' },
    {
      id: 'render-module',
      wgsl: '@vertex fn v() -> @builtin(position) vec4f { return vec4f(); }\n'
        + '@fragment fn f() -> @location(0) vec4f { return vec4f(); }',
    },
  ],
  passes: [
    { id: 'prepare', kind: 'compute' },
    { id: 'draw', kind: 'render' },
  ],
  outputs: ['color'],
};
const runtimeIdentity = {
  schema: 'doppler.chromium-webgpu-runtime-identity/v1',
  host: { platform: 'test', release: 'test', architecture: 'test' },
  browser: { engine: 'chromium', version: 'test', headless: true, args: ['--test'] },
  gpuBackend: { required: 'vulkan', detected: 'vulkan' },
  chromiumGpu: { devices: [], auxAttributes: {}, featureStatus: {} },
  webgpuAdapter: {
    vendor: 'test',
    availableFeatures: [],
    requiredFeatures: [],
    limits: {},
    requiredLimits: {},
  },
};
const successfulCleanup = {
  attempted: true,
  destroyableCount: 2,
  destroyedCount: 2,
  mappedBufferCount: 1,
  unmappedBufferCount: 1,
  errors: [],
  passed: true,
};
const successful = summarizeWgslAuthorBrowserExecution(
  'receipt-test',
  plan,
  runtimeIdentity,
  {
    compilation: [
      { moduleId: 'compute-module', messages: [] },
      { moduleId: 'render-module', messages: [] },
    ],
    runtimeErrors: [],
    executedPassIds: ['prepare', 'draw'],
    outputs: { color: { kind: 'texture', bytes: [0, 1, 2, 3] } },
    cleanup: successfulCleanup,
  }
);
assert.equal(successful.passed, true);
assert.equal(successful.validationErrorsAbsent, true);
assert.match(successful.planSha256, /^[a-f0-9]{64}$/);
assert.match(successful.receiptHash, /^[a-f0-9]{64}$/);
assert.deepEqual(
  summarizeWgslAuthorBrowserExecution(
    'receipt-test',
    plan,
    runtimeIdentity,
    {
      compilation: [
        { moduleId: 'compute-module', messages: [] },
        { moduleId: 'render-module', messages: [] },
      ],
      runtimeErrors: [],
      executedPassIds: ['prepare', 'draw'],
      outputs: { color: { kind: 'texture', bytes: [0, 1, 2, 3] } },
      cleanup: successfulCleanup,
    }
  ),
  successful
);

const compilationFailure = summarizeWgslAuthorBrowserExecution(
  'compile-failure',
  plan,
  runtimeIdentity,
  {
    compilation: [
      {
        moduleId: 'compute-module',
        messages: [{ type: 'error', message: 'bad shader' }],
      },
      { moduleId: 'render-module', messages: [] },
    ],
    runtimeErrors: [],
    executedPassIds: [],
    outputs: {},
    cleanup: successfulCleanup,
  }
);
assert.equal(compilationFailure.passed, false);
assert.equal(compilationFailure.compilation[0].errorCount, 1);

const runtimeFailure = summarizeWgslAuthorBrowserExecution(
  'runtime-failure',
  plan,
  runtimeIdentity,
  {
    compilation: [
      { moduleId: 'compute-module', messages: [] },
      { moduleId: 'render-module', messages: [] },
    ],
    runtimeErrors: ['validation failed'],
    executedPassIds: ['prepare'],
    outputs: {},
    cleanup: successfulCleanup,
  }
);
assert.equal(runtimeFailure.passed, false);
assert.equal(runtimeFailure.validationErrorsAbsent, false);

const cleanupFailure = summarizeWgslAuthorBrowserExecution(
  'cleanup-failure',
  plan,
  runtimeIdentity,
  {
    compilation: [
      { moduleId: 'compute-module', messages: [] },
      { moduleId: 'render-module', messages: [] },
    ],
    runtimeErrors: [],
    executedPassIds: ['prepare', 'draw'],
    outputs: { color: { kind: 'texture', bytes: [0, 1, 2, 3] } },
    cleanup: {
      ...successfulCleanup,
      destroyedCount: 1,
      errors: ['destroy_failed:test'],
      passed: false,
    },
  }
);
assert.equal(cleanupFailure.passed, false);
assert.equal(cleanupFailure.cleanup.passed, false);

const missingCleanup = summarizeWgslAuthorBrowserExecution(
  'cleanup-missing',
  plan,
  runtimeIdentity,
  {
    compilation: [
      { moduleId: 'compute-module', messages: [] },
      { moduleId: 'render-module', messages: [] },
    ],
    runtimeErrors: [],
    executedPassIds: ['prepare', 'draw'],
    outputs: { color: { kind: 'texture', bytes: [0, 1, 2, 3] } },
  }
);
assert.equal(missingCleanup.passed, false);
assert.deepEqual(missingCleanup.cleanup.errors, ['cleanup_result_missing']);

console.log('wgsl-author-browser-executor.test: ok');

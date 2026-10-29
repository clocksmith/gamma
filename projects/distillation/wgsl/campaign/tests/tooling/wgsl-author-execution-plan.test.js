import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { buildWgslAuthorExecutionPlan } from '../../tools/lib/wgsl-author-execution-plan.js';

const literal = (value) => ({ kind: 'literal', value });
const parameter = (name) => ({ kind: 'parameter', name });
const operation = (operator, left, right) => ({
  kind: 'operation',
  operator,
  operands: [left, right],
});
const formats = JSON.parse(
  readFileSync('tools/data/wgsl-author-format-catalog.json', 'utf8')
).formats;

const computePackage = {
  schema: 'doppler.wgsl-author-package/v1',
  requirements: { features: [], limits: [] },
  modules: [{
    id: 'compute-module',
    wgsl: `
@group(0) @binding(0) var<storage, read> sourceValues: array<f32>;
@group(0) @binding(1) var<storage, read_write> resultValues: array<f32>;
@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  if (gid.x < arrayLength(&resultValues)) {
    resultValues[gid.x] = sourceValues[gid.x] + 1.0;
  }
}`.trim(),
  }],
  resources: [
    {
      id: 'source',
      kind: 'storage_buffer',
      access: 'read',
      ownership: 'host',
      descriptor: { byteLength: parameter('byteLength') },
    },
    {
      id: 'result',
      kind: 'storage_buffer',
      access: 'write',
      ownership: 'host',
      descriptor: { byteLength: parameter('byteLength') },
    },
  ],
  passes: [{
    id: 'compute-pass',
    kind: 'compute',
    moduleId: 'compute-module',
    entryPoints: { compute: 'main' },
    constants: [],
    bindings: [
      { group: 0, binding: 0, resourceId: 'source', shaderName: 'sourceValues' },
      { group: 0, binding: 1, resourceId: 'result', shaderName: 'resultValues' },
    ],
    dispatch: {
      x: operation('ceil_div', parameter('elementCount'), literal(64)),
      y: literal(1),
      z: literal(1),
    },
  }],
  outputs: ['result'],
};

const computeContract = {
  parameterNames: ['byteLength', 'elementCount'],
  overrideNames: [],
  requiredStageKinds: ['compute'],
  availableFeatures: [],
  limits: {},
  formats,
  allocationLimits: {
    maxBufferBytes: 1048576,
    maxTextureBytes: 1048576,
    maxTotalBytes: 2097152,
  },
  allowGeneratedResources: false,
  resources: [
    { id: 'source', kind: 'storage_buffer', access: 'read' },
    { id: 'result', kind: 'storage_buffer', access: 'write' },
  ],
};
const computeContext = {
  parameters: { byteLength: 16, elementCount: 129 },
  overrides: {},
  resources: {
    source: { initialization: 'bytes', bytes: Array(16).fill(1) },
    result: { initialization: 'zero' },
  },
};

const computePlan = buildWgslAuthorExecutionPlan(
  computePackage,
  computeContract,
  computeContext
);
assert.equal(computePlan.schema, 'doppler.wgsl-author-execution-plan/v1');
assert.deepEqual(computePlan.passes[0].dispatch, [3, 1, 1]);
assert.deepEqual(computePlan.resources[0].usage, ['copy_dst', 'storage']);
assert.deepEqual(computePlan.resources[1].usage, ['copy_dst', 'copy_src', 'storage']);
assert.deepEqual(computePlan.resources[0].initialization.bytes, Array(16).fill(1));
assert.equal(computePlan.resources[1].initialization.kind, 'zero');

const renderPackage = {
  schema: 'doppler.wgsl-author-package/v1',
  requirements: { features: [], limits: [] },
  modules: [{
    id: 'render-module',
    wgsl: `
@vertex fn vertex_main(@builtin(vertex_index) i: u32) -> @builtin(position) vec4<f32> {
  let p = array<vec2<f32>, 3>(vec2(-1.0, -1.0), vec2(3.0, -1.0), vec2(-1.0, 3.0));
  return vec4(p[i], 0.0, 1.0);
}
@fragment fn fragment_main() -> @location(0) vec4<f32> {
  return vec4(0.25, 0.5, 0.75, 1.0);
}`.trim(),
  }],
  resources: [{
    id: 'color',
    kind: 'render_target',
    access: 'write',
    ownership: 'host',
    descriptor: {
      format: 'rgba8unorm',
      dimension: '2d',
      width: parameter('width'),
      height: parameter('height'),
      depthOrArrayLayers: literal(1),
      mipLevelCount: literal(1),
      sampleCount: 1,
    },
  }],
  passes: [{
    id: 'render-pass',
    kind: 'render',
    moduleId: 'render-module',
    entryPoints: { vertex: 'vertex_main', fragment: 'fragment_main' },
    constants: [],
    bindings: [],
    vertexBuffers: [],
    indexBuffer: null,
    draw: {
      kind: 'direct',
      vertexCount: literal(3),
      instanceCount: literal(1),
      firstVertex: literal(0),
      firstInstance: literal(0),
    },
    primitive: {
      topology: 'triangle-list',
      frontFace: 'ccw',
      cullMode: 'none',
      stripIndexFormat: null,
      unclippedDepth: false,
    },
    multisample: { count: 1, mask: 4294967295, alphaToCoverageEnabled: false },
    viewport: {
      x: literal(0),
      y: literal(0),
      width: parameter('width'),
      height: parameter('height'),
      minDepth: 0,
      maxDepth: 1,
    },
    scissor: {
      x: literal(0),
      y: literal(0),
      width: parameter('width'),
      height: parameter('height'),
    },
    targets: [{
      resourceId: 'color',
      format: 'rgba8unorm',
      loadOp: 'clear',
      storeOp: 'store',
      clearValue: [0, 0, 0, 1],
      blend: null,
      writeMask: 15,
    }],
  }],
  outputs: ['color'],
};
const renderContract = {
  parameterNames: ['width', 'height'],
  overrideNames: [],
  requiredStageKinds: ['render'],
  availableFeatures: [],
  limits: {},
  formats,
  allocationLimits: {
    maxBufferBytes: 1048576,
    maxTextureBytes: 1048576,
    maxTotalBytes: 2097152,
  },
  allowGeneratedResources: false,
  resources: [{ id: 'color', kind: 'render_target', access: 'write' }],
};
const renderPlan = buildWgslAuthorExecutionPlan(renderPackage, renderContract, {
  parameters: { width: 2, height: 3 },
  overrides: {},
  resources: { color: { initialization: 'zero' } },
});
assert.deepEqual(renderPlan.resources[0].descriptor.size, {
  width: 2,
  height: 3,
  depthOrArrayLayers: 1,
});
assert.equal(renderPlan.resources[0].descriptor.copy.tightBytesPerRow, 8);
assert.equal(renderPlan.resources[0].descriptor.copy.tightByteLength, 24);
assert.deepEqual(renderPlan.resources[0].usage, [
  'copy_dst',
  'copy_src',
  'render_attachment',
  'texture_binding',
]);
assert.equal(renderPlan.passes[0].draw.vertexCount, 3);

assert.throws(
  () => buildWgslAuthorExecutionPlan(computePackage, computeContract, {
    ...computeContext,
    resources: { result: { initialization: 'zero' } },
  }),
  /Host resource payload is missing: source/
);
assert.throws(
  () => buildWgslAuthorExecutionPlan(computePackage, computeContract, {
    ...computeContext,
    resources: {
      ...computeContext.resources,
      source: { initialization: 'bytes', bytes: [1, 2] },
    },
  }),
  /byte length mismatch/
);
assert.throws(
  () => buildWgslAuthorExecutionPlan(computePackage, computeContract, {
    ...computeContext,
    parameters: { ...computeContext.parameters, byteLength: 15 },
  }),
  /aligned to four bytes/
);
const unsupportedFormat = structuredClone(renderPackage);
unsupportedFormat.resources[0].descriptor.format = 'depth24plus';
unsupportedFormat.passes[0].targets[0].format = 'depth24plus';
assert.throws(
  () => buildWgslAuthorExecutionPlan(unsupportedFormat, renderContract, {
    parameters: { width: 2, height: 3 },
    overrides: {},
    resources: { color: { initialization: 'zero' } },
  }),
  /Unsupported WGSL author texture format/
);

console.log('wgsl-author-execution-plan.test: ok');

import assert from 'node:assert/strict';

import {
  buildWgslAuthorPrompt,
  evaluateWgslAuthorExpression,
  parseWgslAuthorPackageResponse,
  validateWgslAuthorPackage,
} from '../../tools/lib/wgsl-author-package.js';

const literal = (value) => ({ kind: 'literal', value });
const parameter = (name) => ({ kind: 'parameter', name });
const operation = (operator, left, right) => ({
  kind: 'operation',
  operator,
  operands: [left, right],
});

const computePackage = {
  schema: 'doppler.wgsl-author-package/v1',
  requirements: { features: [], limits: [] },
  modules: [
    {
      id: 'compute-module',
      wgsl: `
@group(0) @binding(0) var<storage, read> inputData: array<f32>;
@group(0) @binding(1) var<storage, read_write> outputData: array<f32>;

@compute @workgroup_size(64)
fn compute_main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let index = gid.x;
  if (index < arrayLength(&outputData)) {
    outputData[index] = inputData[index] * 2.0;
  }
}`.trim(),
    },
  ],
  resources: [
    {
      id: 'input',
      kind: 'storage_buffer',
      access: 'read',
      ownership: 'host',
      descriptor: { byteLength: parameter('byteLength') },
    },
    {
      id: 'output',
      kind: 'storage_buffer',
      access: 'write',
      ownership: 'host',
      descriptor: { byteLength: parameter('byteLength') },
    },
  ],
  passes: [
    {
      id: 'compute-pass',
      kind: 'compute',
      moduleId: 'compute-module',
      entryPoints: { compute: 'compute_main' },
      constants: [],
      bindings: [
        { group: 0, binding: 0, resourceId: 'input', shaderName: 'inputData' },
        { group: 0, binding: 1, resourceId: 'output', shaderName: 'outputData' },
      ],
      dispatch: {
        x: operation('ceil_div', parameter('elementCount'), literal(64)),
        y: literal(1),
        z: literal(1),
      },
    },
  ],
  outputs: ['output'],
};

const computeContract = {
  parameterNames: ['byteLength', 'elementCount'],
  overrideNames: [],
  requiredStageKinds: ['compute'],
  allowGeneratedResources: false,
  resources: [
    { id: 'input', kind: 'storage_buffer', access: 'read' },
    { id: 'output', kind: 'storage_buffer', access: 'write' },
  ],
};

assert.deepEqual(validateWgslAuthorPackage(computePackage, computeContract), {
  ok: true,
  violations: [],
});
assert.deepEqual(
  parseWgslAuthorPackageResponse(JSON.stringify(computePackage), computeContract).violations,
  []
);

const renderPackage = {
  schema: 'doppler.wgsl-author-package/v1',
  requirements: { features: [], limits: [] },
  modules: [
    {
      id: 'render-module',
      wgsl: `
struct Scene { tint: vec4<f32> };
@group(0) @binding(0) var<uniform> scene: Scene;

@vertex
fn vertex_main(@builtin(vertex_index) index: u32) -> @builtin(position) vec4<f32> {
  let points = array<vec2<f32>, 3>(
    vec2<f32>(-1.0, -1.0),
    vec2<f32>(3.0, -1.0),
    vec2<f32>(-1.0, 3.0)
  );
  return vec4<f32>(points[index], 0.0, 1.0);
}

@fragment
fn fragment_main() -> @location(0) vec4<f32> {
  return scene.tint;
}`.trim(),
    },
  ],
  resources: [
    {
      id: 'scene',
      kind: 'uniform_buffer',
      access: 'read',
      ownership: 'host',
      descriptor: { byteLength: literal(16) },
    },
    {
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
    },
  ],
  passes: [
    {
      id: 'render-pass',
      kind: 'render',
      moduleId: 'render-module',
      entryPoints: { vertex: 'vertex_main', fragment: 'fragment_main' },
      constants: [],
      bindings: [
        { group: 0, binding: 0, resourceId: 'scene', shaderName: 'scene' },
      ],
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
    },
  ],
  outputs: ['color'],
};

const renderContract = {
  parameterNames: ['width', 'height'],
  overrideNames: [],
  requiredStageKinds: ['render'],
  allowGeneratedResources: false,
  resources: [
    { id: 'scene', kind: 'uniform_buffer', access: 'read' },
    { id: 'color', kind: 'render_target', access: 'write' },
  ],
};

assert.equal(validateWgslAuthorPackage(renderPackage, renderContract).ok, true);

const multiPassPackage = structuredClone(renderPackage);
multiPassPackage.modules.unshift(structuredClone(computePackage.modules[0]));
multiPassPackage.resources.unshift({
  id: 'generated-values',
  kind: 'storage_buffer',
  access: 'read_write',
  ownership: 'generated',
  descriptor: { byteLength: parameter('byteLength') },
});
multiPassPackage.modules[0].wgsl = multiPassPackage.modules[0].wgsl
  .replace('inputData', 'generatedValues')
  .replace('inputData', 'generatedValues')
  .replace('@group(0) @binding(1) var<storage, read_write> outputData: array<f32>;\n', '')
  .replace('outputData', 'generatedValues')
  .replace('outputData', 'generatedValues');
multiPassPackage.passes.unshift({
  id: 'prepare-pass',
  kind: 'compute',
  moduleId: 'compute-module',
  entryPoints: { compute: 'compute_main' },
  constants: [],
  bindings: [
    { group: 0, binding: 0, resourceId: 'generated-values', shaderName: 'generatedValues' },
  ],
  dispatch: {
    x: operation('ceil_div', parameter('elementCount'), literal(64)),
    y: literal(1),
    z: literal(1),
  },
});
const multiPassContract = {
  ...renderContract,
  parameterNames: ['width', 'height', 'byteLength', 'elementCount'],
  requiredStageKinds: ['compute', 'render'],
  allowGeneratedResources: true,
};
assert.equal(validateWgslAuthorPackage(multiPassPackage, multiPassContract).ok, true);

const offscreenPackage = structuredClone(renderPackage);
offscreenPackage.modules.push({
  id: 'postprocess-module',
  wgsl: `
@group(0) @binding(0) var offscreenColor: texture_2d<f32>;

struct VertexOutput {
  @builtin(position) position: vec4<f32>,
  @location(0) uv: vec2<f32>,
};

@vertex
fn vertex_main(@builtin(vertex_index) index: u32) -> VertexOutput {
  let positions = array<vec2<f32>, 3>(
    vec2<f32>(-1.0, -1.0),
    vec2<f32>(3.0, -1.0),
    vec2<f32>(-1.0, 3.0)
  );
  let position = positions[index];
  var output: VertexOutput;
  output.position = vec4<f32>(position, 0.0, 1.0);
  output.uv = position * vec2<f32>(0.5, -0.5) + vec2<f32>(0.5);
  return output;
}

@fragment
fn fragment_main(input: VertexOutput) -> @location(0) vec4<f32> {
  let size = vec2<i32>(textureDimensions(offscreenColor));
  let coordinate = clamp(vec2<i32>(input.uv * vec2<f32>(size)), vec2<i32>(0), size - 1);
  return textureLoad(offscreenColor, coordinate, 0);
}`.trim(),
});
offscreenPackage.resources[1].access = 'read_write';
offscreenPackage.resources.push({
  ...structuredClone(offscreenPackage.resources[1]),
  id: 'postprocess-color',
  access: 'write',
});
offscreenPackage.passes.push({
  ...structuredClone(offscreenPackage.passes[0]),
  id: 'postprocess-pass',
  moduleId: 'postprocess-module',
  bindings: [{
    group: 0,
    binding: 0,
    resourceId: 'color',
    shaderName: 'offscreenColor',
  }],
  targets: [{
    ...structuredClone(offscreenPackage.passes[0].targets[0]),
    resourceId: 'postprocess-color',
  }],
});
offscreenPackage.outputs = ['postprocess-color'];
const offscreenContract = {
  ...renderContract,
  resources: [
    renderContract.resources[0],
    { id: 'color', kind: 'render_target', access: 'read_write' },
    { id: 'postprocess-color', kind: 'render_target', access: 'write' },
  ],
};
assert.deepEqual(validateWgslAuthorPackage(offscreenPackage, offscreenContract), {
  ok: true,
  violations: [],
});

const indexedPackage = structuredClone(renderPackage);
indexedPackage.resources.splice(1, 0,
  {
    id: 'vertices',
    kind: 'vertex_buffer',
    access: 'read',
    ownership: 'host',
    descriptor: {
      byteLength: parameter('vertexBytes'),
      arrayStride: 8,
      stepMode: 'vertex',
      attributes: [{ shaderLocation: 0, offset: 0, format: 'float32x2' }],
    },
  },
  {
    id: 'indices',
    kind: 'index_buffer',
    access: 'read',
    ownership: 'host',
    descriptor: { byteLength: parameter('indexBytes'), indexFormat: 'uint32' },
  });
indexedPackage.passes[0].vertexBuffers = [{ slot: 0, resourceId: 'vertices' }];
indexedPackage.passes[0].indexBuffer = { resourceId: 'indices' };
indexedPackage.passes[0].draw = {
  kind: 'indexed',
  indexCount: parameter('indexCount'),
  instanceCount: literal(1),
  firstIndex: literal(0),
  baseVertex: literal(0),
  firstInstance: literal(0),
};
const indexedContract = {
  ...renderContract,
  parameterNames: ['width', 'height', 'vertexBytes', 'indexBytes', 'indexCount'],
  resources: [
    ...renderContract.resources,
    { id: 'vertices', kind: 'vertex_buffer', access: 'read' },
    { id: 'indices', kind: 'index_buffer', access: 'read' },
  ],
};
assert.equal(validateWgslAuthorPackage(indexedPackage, indexedContract).ok, true);

const badBinding = structuredClone(computePackage);
badBinding.passes[0].bindings[0].shaderName = 'missingInput';
assert.equal(
  validateWgslAuthorPackage(badBinding, computeContract).violations.includes(
    'passes[0].bindings[0]:wgsl_declaration_missing'
  ),
  true
);

const unknownParameter = structuredClone(computePackage);
unknownParameter.passes[0].dispatch.x = parameter('unboundCount');
assert.equal(
  validateWgslAuthorPackage(unknownParameter, computeContract).violations.includes(
    'passes[0].dispatch.x:parameter_unknown'
  ),
  true
);

const wrongTargetFormat = structuredClone(renderPackage);
wrongTargetFormat.passes[0].targets[0].format = 'bgra8unorm';
assert.equal(
  validateWgslAuthorPackage(wrongTargetFormat, renderContract).violations.includes(
    'passes[0].targets[0]:format_mismatch'
  ),
  true
);

const unavailableFeature = structuredClone(computePackage);
unavailableFeature.requirements.features = ['shader-f16'];
assert.equal(
  validateWgslAuthorPackage(unavailableFeature, {
    ...computeContract,
    availableFeatures: [],
  }).violations.includes('requirements.features[0]:feature_unavailable'),
  true
);

for (const invalid of [
  { ...computePackage, modules: {} },
  { ...computePackage, resources: {} },
  { ...computePackage, passes: {} },
  { ...computePackage, passes: [null] },
  { ...computePackage, passes: [{ ...computePackage.passes[0], bindings: {} }] },
]) {
  assert.doesNotThrow(() => validateWgslAuthorPackage(invalid, computeContract));
  assert.equal(validateWgslAuthorPackage(invalid, computeContract).ok, false);
}

assert.deepEqual(
  parseWgslAuthorPackageResponse('```json\n{}\n```', computeContract).violations,
  ['markdown_fence', 'malformed_json']
);
assert.equal(parseWgslAuthorPackageResponse('{', computeContract).ok, false);
assert.equal(parseWgslAuthorPackageResponse(null, computeContract).ok, false);

assert.equal(
  evaluateWgslAuthorExpression(
    operation('ceil_div', parameter('elementCount'), literal(64)),
    { parameters: { elementCount: 129 } }
  ),
  3
);
assert.equal(
  evaluateWgslAuthorExpression(operation('max', literal(7), literal(0))),
  7
);
assert.throws(
  () => evaluateWgslAuthorExpression(operation('ceil_div', literal(7), literal(0))),
  /denominator must be positive/
);

const prompt = buildWgslAuthorPrompt({
  taskId: 'author-compute-001',
  objective: 'Double every input value.',
  resources: computeContract.resources,
  parameters: computeContract.parameterNames,
  acceptance: { oracle: 'double_f32' },
}, {
  responseContract: 'wgsl_author_package_v1',
});
assert.match(prompt, /doppler\.wgsl-author-package\/v1/);
assert.match(prompt, /Double every input value\./);
assert.doesNotMatch(prompt, /```/);

console.log('wgsl-author-package.test: ok');

const literal = (value) => ({ kind: 'literal', value });
const parameter = (name) => ({ kind: 'parameter', name });
const override = (name) => ({ kind: 'override', name });
const operation = (operator, left, right) => ({
  kind: 'operation',
  operator,
  operands: [left, right],
});

const rgba8 = (red, green, blue, alpha = 255) => [red, green, blue, alpha];

function bytesFromValues(values, kind) {
  const bytes = new Uint8Array(values.length * 4);
  const view = new DataView(bytes.buffer);
  for (let index = 0; index < values.length; index += 1) {
    if (kind === 'f32') view.setFloat32(index * 4, Number(values[index]), true);
    else view.setUint32(index * 4, Number(values[index]), true);
  }
  return [...bytes];
}

function bytesFromFloat32(values) {
  return bytesFromValues(values, 'f32');
}

function bytesFromUint32(values) {
  return bytesFromValues(values, 'u32');
}

function bufferResource(id, kind, access, byteLength, ownership = 'host', descriptor = {}) {
  return {
    id,
    kind,
    access,
    ownership,
    descriptor: { byteLength, ...descriptor },
  };
}

function textureResource(id, kind, access, format, width, height, ownership = 'host') {
  return {
    id,
    kind,
    access,
    ownership,
    descriptor: {
      format,
      dimension: '2d',
      width,
      height,
      depthOrArrayLayers: literal(1),
      mipLevelCount: literal(1),
      sampleCount: 1,
      ...(kind === 'sampled_texture' ? { sampleType: 'float' } : {}),
    },
  };
}

function samplerResource(id = 'linear-sampler', filter = 'nearest') {
  return {
    id,
    kind: 'sampler',
    access: 'read',
    ownership: 'host',
    descriptor: {
      samplerType: 'filtering',
      addressModeU: 'clamp-to-edge',
      addressModeV: 'clamp-to-edge',
      addressModeW: 'clamp-to-edge',
      magFilter: filter,
      minFilter: filter,
      mipmapFilter: filter,
      lodMinClamp: 0,
      lodMaxClamp: 0,
      compare: null,
      maxAnisotropy: 1,
    },
  };
}

function binding(group, slot, resourceId, shaderName) {
  return { group, binding: slot, resourceId, shaderName };
}

function computePass(moduleId, bindings, dispatch, constants = []) {
  return {
    id: 'compute-pass',
    kind: 'compute',
    moduleId,
    entryPoints: { compute: 'compute_main' },
    constants,
    bindings,
    dispatch,
  };
}

function directDraw(vertexCount = literal(3), instanceCount = literal(1)) {
  return {
    kind: 'direct',
    vertexCount,
    instanceCount,
    firstVertex: literal(0),
    firstInstance: literal(0),
  };
}

function renderPass(options) {
  return {
    id: options.id || 'render-pass',
    kind: 'render',
    moduleId: options.moduleId,
    entryPoints: { vertex: 'vertex_main', fragment: 'fragment_main' },
    constants: options.constants || [],
    bindings: options.bindings || [],
    vertexBuffers: options.vertexBuffers || [],
    indexBuffer: options.indexBuffer || null,
    draw: options.draw || directDraw(),
    primitive: {
      topology: options.topology || 'triangle-list',
      frontFace: 'ccw',
      cullMode: 'none',
      stripIndexFormat: null,
      unclippedDepth: false,
    },
    multisample: { count: 1, mask: 0xffffffff, alphaToCoverageEnabled: false },
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
      resourceId: options.targetId || 'color',
      format: 'rgba8unorm',
      loadOp: 'clear',
      storeOp: 'store',
      clearValue: [0, 0, 0, 1],
      blend: null,
      writeMask: 15,
    }],
  };
}

function packageValue(modules, resources, passes, outputs) {
  return {
    schema: 'doppler.wgsl-author-package/v1',
    requirements: { features: [], limits: [] },
    modules,
    resources,
    passes,
    outputs,
  };
}

function contractFor(resources, parameterNames, requiredStageKinds) {
  return {
    parameterNames,
    overrideNames: ['WORKGROUP_SIZE'],
    requiredStageKinds,
    allowGeneratedResources: false,
    resources: resources.map(({ id, kind, access }) => ({ id, kind, access })),
  };
}

function taskResult(family, variant, objective, package_, contract, context, oracle) {
  return {
    familyId: family.id,
    populationRole: family.populationRole,
    pipelineKind: family.pipelineKind,
    variant,
    objective,
    packageValue: package_,
    contract,
    context,
    oracle,
    acceptance: {
      compilation: true,
      actualExecution: true,
      oracle: family.verification.oracle,
      deterministicReplay: true,
      bufferBounds: true,
      metamorphic: true,
      historicalRegressions: true,
      requiredVariations: family.verification.requiredVariations,
    },
  };
}

function computeShape(variant) {
  const lengths = [8, 11, 17, 5];
  const workgroups = [4, 8, 4, 2];
  const index = variant % lengths.length;
  return { length: lengths[index], workgroupSize: workgroups[index] };
}

function bufferMap(family, variant) {
  const { length, workgroupSize } = computeShape(variant);
  const source = Array.from({ length }, (_, index) => ((index * 3 + variant) % 13) - 6);
  const expected = source.map((value) => value * 1.5 - 0.25);
  const resources = [
    bufferResource('source', 'storage_buffer', 'read', parameter('byteLength')),
    bufferResource('result', 'storage_buffer', 'write', parameter('byteLength')),
  ];
  const wgsl = `
override WORKGROUP_SIZE: u32 = 4u;

@group(0) @binding(0) var<storage, read> source_values: array<f32>;
@group(0) @binding(1) var<storage, read_write> result_values: array<f32>;

@compute @workgroup_size(WORKGROUP_SIZE, 1, 1)
fn compute_main(@builtin(global_invocation_id) global_id: vec3<u32>) {
  let index = global_id.x;
  if (index >= arrayLength(&result_values)) {
    return;
  }
  result_values[index] = source_values[index] * 1.5 - 0.25;
}`.trim();
  const package_ = packageValue(
    [{ id: 'buffer-map-module', wgsl }],
    resources,
    [computePass('buffer-map-module', [
      binding(0, 0, 'source', 'source_values'),
      binding(0, 1, 'result', 'result_values'),
    ], {
      x: operation('ceil_div', parameter('elementCount'), override('WORKGROUP_SIZE')),
      y: literal(1),
      z: literal(1),
    }, [{ name: 'WORKGROUP_SIZE', value: override('WORKGROUP_SIZE') }])],
    ['result']
  );
  return taskResult(
    family,
    variant,
    'Transform every source f32 value with result = source * 1.5 - 0.25 while guarding the tail dispatch.',
    package_,
    contractFor(resources, ['byteLength', 'elementCount'], ['compute']),
    {
      parameters: { byteLength: length * 4, elementCount: length },
      overrides: { WORKGROUP_SIZE: workgroupSize },
      resources: {
        source: { initialization: 'bytes', bytes: bytesFromFloat32(source) },
        result: { initialization: 'zero' },
      },
    },
    { kind: 'f32_sequence', resourceId: 'result', expected, absTolerance: 1e-6, relTolerance: 1e-6 }
  );
}

function tiledMatrixTransform(family, variant) {
  const side = variant % 2 === 0 ? 4 : 3;
  const workgroupSize = side;
  const values = Array.from({ length: side * side }, (_, index) => index + variant * 0.5);
  const expected = Array.from({ length: values.length }, (_, index) => {
    const row = Math.floor(index / side);
    const column = index % side;
    return values[column * side + row];
  });
  const resources = [
    bufferResource('source', 'storage_buffer', 'read', parameter('byteLength')),
    bufferResource('result', 'storage_buffer', 'write', parameter('byteLength')),
    bufferResource('matrix-config', 'uniform_buffer', 'read', literal(16)),
  ];
  const wgsl = `
override WORKGROUP_SIZE: u32 = 4u;

struct MatrixConfig {
  width: u32,
  height: u32,
  reserved_0: u32,
  reserved_1: u32,
}

@group(0) @binding(0) var<storage, read> source_values: array<f32>;
@group(0) @binding(1) var<storage, read_write> result_values: array<f32>;
@group(0) @binding(2) var<uniform> matrix_config: MatrixConfig;
var<workgroup> tile: array<f32, 64>;

@compute @workgroup_size(WORKGROUP_SIZE, WORKGROUP_SIZE, 1)
fn compute_main(
  @builtin(local_invocation_id) local_id: vec3<u32>,
  @builtin(global_invocation_id) global_id: vec3<u32>,
) {
  let local_index = local_id.y * WORKGROUP_SIZE + local_id.x;
  let in_bounds = global_id.x < matrix_config.width && global_id.y < matrix_config.height;
  if (in_bounds) {
    tile[local_index] = source_values[global_id.y * matrix_config.width + global_id.x];
  } else {
    tile[local_index] = 0.0;
  }
  workgroupBarrier();
  if (!in_bounds) {
    return;
  }
  result_values[global_id.x * matrix_config.height + global_id.y] = tile[local_index];
}`.trim();
  const package_ = packageValue(
    [{ id: 'matrix-module', wgsl }],
    resources,
    [computePass('matrix-module', [
      binding(0, 0, 'source', 'source_values'),
      binding(0, 1, 'result', 'result_values'),
      binding(0, 2, 'matrix-config', 'matrix_config'),
    ], {
      x: operation('ceil_div', parameter('width'), override('WORKGROUP_SIZE')),
      y: operation('ceil_div', parameter('height'), override('WORKGROUP_SIZE')),
      z: literal(1),
    }, [{ name: 'WORKGROUP_SIZE', value: override('WORKGROUP_SIZE') }])],
    ['result']
  );
  return taskResult(
    family,
    variant,
    'Transpose a square f32 matrix through workgroup memory and preserve boundary-tile safety.',
    package_,
    contractFor(resources, ['byteLength', 'width', 'height'], ['compute']),
    {
      parameters: { byteLength: values.length * 4, width: side, height: side },
      overrides: { WORKGROUP_SIZE: workgroupSize },
      resources: {
        source: { initialization: 'bytes', bytes: bytesFromFloat32(values) },
        result: { initialization: 'zero' },
        'matrix-config': {
          initialization: 'bytes',
          bytes: bytesFromUint32([side, side, 0, 0]),
        },
      },
    },
    { kind: 'f32_sequence', resourceId: 'result', expected, absTolerance: 1e-6, relTolerance: 1e-6 }
  );
}

function atomicHistogram(family, variant) {
  const shape = computeShape(variant);
  const binCount = 4;
  const { length } = shape;
  const workgroupSize = Math.max(shape.workgroupSize, binCount);
  const input = Array.from({ length }, (_, index) => (index * 3 + variant) % binCount);
  const expected = Array(binCount).fill(0);
  for (const value of input) expected[value] += 1;
  const resources = [
    bufferResource('samples', 'storage_buffer', 'read', parameter('inputBytes')),
    bufferResource('histogram', 'storage_buffer', 'write', parameter('outputBytes')),
  ];
  const wgsl = `
override WORKGROUP_SIZE: u32 = 4u;
const BIN_COUNT: u32 = 4u;

@group(0) @binding(0) var<storage, read> samples: array<u32>;
@group(0) @binding(1) var<storage, read_write> histogram: array<atomic<u32>>;
var<workgroup> local_histogram: array<atomic<u32>, 4>;

@compute @workgroup_size(WORKGROUP_SIZE, 1, 1)
fn compute_main(
  @builtin(global_invocation_id) global_id: vec3<u32>,
  @builtin(local_invocation_id) local_id: vec3<u32>,
) {
  if (local_id.x < BIN_COUNT) {
    atomicStore(&local_histogram[local_id.x], 0u);
  }
  workgroupBarrier();
  if (global_id.x < arrayLength(&samples)) {
    atomicAdd(&local_histogram[samples[global_id.x] % BIN_COUNT], 1u);
  }
  workgroupBarrier();
  if (local_id.x < BIN_COUNT) {
    atomicAdd(&histogram[local_id.x], atomicLoad(&local_histogram[local_id.x]));
  }
}`.trim();
  const package_ = packageValue(
    [{ id: 'histogram-module', wgsl }],
    resources,
    [computePass('histogram-module', [
      binding(0, 0, 'samples', 'samples'),
      binding(0, 1, 'histogram', 'histogram'),
    ], {
      x: operation('ceil_div', parameter('elementCount'), override('WORKGROUP_SIZE')),
      y: literal(1),
      z: literal(1),
    }, [{ name: 'WORKGROUP_SIZE', value: override('WORKGROUP_SIZE') }])],
    ['histogram']
  );
  return taskResult(
    family,
    variant,
    'Build a deterministic four-bin u32 histogram with workgroup-local atomics and a global merge.',
    package_,
    contractFor(resources, ['inputBytes', 'outputBytes', 'elementCount'], ['compute']),
    {
      parameters: { inputBytes: length * 4, outputBytes: binCount * 4, elementCount: length },
      overrides: { WORKGROUP_SIZE: workgroupSize },
      resources: {
        samples: { initialization: 'bytes', bytes: bytesFromUint32(input) },
        histogram: { initialization: 'zero' },
      },
    },
    { kind: 'u32_sequence', resourceId: 'histogram', expected }
  );
}

function reduction(family, variant, segmented) {
  const workgroupSize = variant % 2 === 0 ? 4 : 8;
  const length = segmented ? (variant % 2 === 0 ? 12 : 15) : (variant % 2 === 0 ? 10 : 13);
  const values = Array.from({ length }, (_, index) => (index % 7) - 2 + variant * 0.125);
  const segmentCount = segmented ? 3 : Math.ceil(length / workgroupSize);
  const expected = segmented
    ? Array.from({ length: segmentCount }, (_, segment) => values
      .filter((_, index) => index % segmentCount === segment)
      .reduce((sum, value) => sum + value, 0))
    : Array.from({ length: segmentCount }, (_, group) => values
      .slice(group * workgroupSize, (group + 1) * workgroupSize)
      .reduce((sum, value) => sum + value, 0));
  const resources = [
    bufferResource('source', 'storage_buffer', 'read', parameter('inputBytes')),
    bufferResource('partials', 'storage_buffer', 'write', parameter('outputBytes')),
    bufferResource('reduce-config', 'uniform_buffer', 'read', literal(16)),
  ];
  const wgsl = segmented ? `
override WORKGROUP_SIZE: u32 = 4u;

struct ReduceConfig {
  element_count: u32,
  segment_count: u32,
  reserved_0: u32,
  reserved_1: u32,
}

@group(0) @binding(0) var<storage, read> source_values: array<f32>;
@group(0) @binding(1) var<storage, read_write> segment_sums: array<f32>;
@group(0) @binding(2) var<uniform> reduce_config: ReduceConfig;
var<workgroup> scratch: array<f32, 64>;

@compute @workgroup_size(WORKGROUP_SIZE, 1, 1)
fn compute_main(
  @builtin(workgroup_id) workgroup_id: vec3<u32>,
  @builtin(local_invocation_id) local_id: vec3<u32>,
) {
  let segment = workgroup_id.x;
  var sum = 0.0;
  var index = local_id.x;
  loop {
    if (index >= reduce_config.element_count) { break; }
    if (index % reduce_config.segment_count == segment) {
      sum += source_values[index];
    }
    index += WORKGROUP_SIZE;
  }
  scratch[local_id.x] = sum;
  workgroupBarrier();
  var stride = WORKGROUP_SIZE / 2u;
  loop {
    if (stride == 0u) { break; }
    if (local_id.x < stride) { scratch[local_id.x] += scratch[local_id.x + stride]; }
    workgroupBarrier();
    stride /= 2u;
  }
  if (local_id.x == 0u && segment < reduce_config.segment_count) {
    segment_sums[segment] = scratch[0];
  }
}`.trim() : `
override WORKGROUP_SIZE: u32 = 4u;

struct ReduceConfig {
  element_count: u32,
  group_count: u32,
  reserved_0: u32,
  reserved_1: u32,
}

@group(0) @binding(0) var<storage, read> source_values: array<f32>;
@group(0) @binding(1) var<storage, read_write> partial_sums: array<f32>;
@group(0) @binding(2) var<uniform> reduce_config: ReduceConfig;
var<workgroup> scratch: array<f32, 64>;

@compute @workgroup_size(WORKGROUP_SIZE, 1, 1)
fn compute_main(
  @builtin(global_invocation_id) global_id: vec3<u32>,
  @builtin(workgroup_id) workgroup_id: vec3<u32>,
  @builtin(local_invocation_id) local_id: vec3<u32>,
) {
  scratch[local_id.x] = select(0.0, source_values[global_id.x], global_id.x < reduce_config.element_count);
  workgroupBarrier();
  var stride = WORKGROUP_SIZE / 2u;
  loop {
    if (stride == 0u) { break; }
    if (local_id.x < stride) { scratch[local_id.x] += scratch[local_id.x + stride]; }
    workgroupBarrier();
    stride /= 2u;
  }
  if (local_id.x == 0u && workgroup_id.x < reduce_config.group_count) {
    partial_sums[workgroup_id.x] = scratch[0];
  }
}`.trim();
  const package_ = packageValue(
    [{ id: 'reduction-module', wgsl }],
    resources,
    [computePass('reduction-module', [
      binding(0, 0, 'source', 'source_values'),
      binding(0, 1, 'partials', segmented ? 'segment_sums' : 'partial_sums'),
      binding(0, 2, 'reduce-config', 'reduce_config'),
    ], {
      x: segmented
        ? parameter('segmentCount')
        : operation('ceil_div', parameter('elementCount'), override('WORKGROUP_SIZE')),
      y: literal(1),
      z: literal(1),
    }, [{ name: 'WORKGROUP_SIZE', value: override('WORKGROUP_SIZE') }])],
    ['partials']
  );
  return taskResult(
    family,
    variant,
    segmented
      ? 'Reduce interleaved irregular segments into one deterministic f32 sum per segment.'
      : 'Reduce each complete or partial workgroup into one deterministic f32 partial sum.',
    package_,
    contractFor(resources, ['inputBytes', 'outputBytes', 'elementCount', 'segmentCount'], ['compute']),
    {
      parameters: {
        inputBytes: length * 4,
        outputBytes: segmentCount * 4,
        elementCount: length,
        segmentCount,
      },
      overrides: { WORKGROUP_SIZE: workgroupSize },
      resources: {
        source: { initialization: 'bytes', bytes: bytesFromFloat32(values) },
        partials: { initialization: 'zero' },
        'reduce-config': {
          initialization: 'bytes',
          bytes: bytesFromUint32([length, segmentCount, 0, 0]),
        },
      },
    },
    { kind: 'f32_sequence', resourceId: 'partials', expected, absTolerance: 1e-5, relTolerance: 1e-6 }
  );
}

function particleIntegration(family, variant) {
  const { length, workgroupSize } = computeShape(variant);
  const dt = 0.125;
  const source = Array.from({ length }, (_, index) => [
    ((index * 3) % 10) / 10,
    ((index * 7) % 10) / 10,
    ((index % 3) - 1) * 0.2,
    (((index + 1) % 3) - 1) * 0.15,
  ]).flat();
  const expected = [];
  for (let index = 0; index < length; index += 1) {
    const offset = index * 4;
    expected.push(
      Math.min(1, Math.max(0, source[offset] + source[offset + 2] * dt)),
      Math.min(1, Math.max(0, source[offset + 1] + source[offset + 3] * dt)),
      source[offset + 2],
      source[offset + 3]
    );
  }
  const resources = [
    bufferResource('particles', 'storage_buffer', 'read', parameter('byteLength')),
    bufferResource('next-particles', 'storage_buffer', 'write', parameter('byteLength')),
    bufferResource('integration-config', 'uniform_buffer', 'read', literal(16)),
  ];
  const wgsl = `
override WORKGROUP_SIZE: u32 = 4u;

struct Particle { position: vec2<f32>, velocity: vec2<f32> }
struct IntegrationConfig { delta_time: f32, domain_max: f32, count: u32, reserved: u32 }

@group(0) @binding(0) var<storage, read> particles: array<Particle>;
@group(0) @binding(1) var<storage, read_write> next_particles: array<Particle>;
@group(0) @binding(2) var<uniform> integration_config: IntegrationConfig;

@compute @workgroup_size(WORKGROUP_SIZE, 1, 1)
fn compute_main(@builtin(global_invocation_id) global_id: vec3<u32>) {
  let index = global_id.x;
  if (index >= integration_config.count) { return; }
  let particle = particles[index];
  next_particles[index].position = clamp(
    particle.position + particle.velocity * integration_config.delta_time,
    vec2<f32>(0.0),
    vec2<f32>(integration_config.domain_max)
  );
  next_particles[index].velocity = particle.velocity;
}`.trim();
  const config = new ArrayBuffer(16);
  const configView = new DataView(config);
  configView.setFloat32(0, dt, true);
  configView.setFloat32(4, 1, true);
  configView.setUint32(8, length, true);
  configView.setUint32(12, 0, true);
  const package_ = packageValue(
    [{ id: 'particle-module', wgsl }],
    resources,
    [computePass('particle-module', [
      binding(0, 0, 'particles', 'particles'),
      binding(0, 1, 'next-particles', 'next_particles'),
      binding(0, 2, 'integration-config', 'integration_config'),
    ], {
      x: operation('ceil_div', parameter('particleCount'), override('WORKGROUP_SIZE')),
      y: literal(1),
      z: literal(1),
    }, [{ name: 'WORKGROUP_SIZE', value: override('WORKGROUP_SIZE') }])],
    ['next-particles']
  );
  return taskResult(
    family,
    variant,
    'Integrate packed particle position and velocity state under an explicit bounded domain.',
    package_,
    contractFor(resources, ['byteLength', 'particleCount'], ['compute']),
    {
      parameters: { byteLength: length * 16, particleCount: length },
      overrides: { WORKGROUP_SIZE: workgroupSize },
      resources: {
        particles: { initialization: 'bytes', bytes: bytesFromFloat32(source) },
        'next-particles': { initialization: 'zero' },
        'integration-config': { initialization: 'bytes', bytes: [...new Uint8Array(config)] },
      },
    },
    { kind: 'f32_sequence', resourceId: 'next-particles', expected, absTolerance: 1e-6, relTolerance: 1e-6 }
  );
}

export const WGSL_WRITER_V3_FAMILY_BUILDERS = Object.freeze({
  'buffer-map': bufferMap,
  'tiled-matrix-transform': tiledMatrixTransform,
  'atomic-histogram': atomicHistogram,
  'bounded-reduction': (family, variant) => reduction(family, variant, false),
  'segmented-reduction': (family, variant) => reduction(family, variant, true),
  'particle-integration': particleIntegration,
});

export {
  binding,
  bufferResource,
  bytesFromFloat32,
  bytesFromUint32,
  computePass,
  contractFor,
  directDraw,
  literal,
  operation,
  override,
  packageValue,
  parameter,
  renderPass,
  rgba8,
  samplerResource,
  taskResult,
  textureResource,
};

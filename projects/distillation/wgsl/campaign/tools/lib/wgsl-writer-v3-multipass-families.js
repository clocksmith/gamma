import {
  binding,
  bufferResource,
  bytesFromFloat32,
  computePass,
  contractFor,
  directDraw,
  literal,
  operation,
  override,
  packageValue,
  parameter,
  renderPass,
  samplerResource,
  taskResult,
  textureResource,
} from './wgsl-writer-v3-family-builders.js';

function shape(variant) {
  return variant % 2 === 0
    ? { width: 3, height: 2 }
    : { width: 4, height: 3 };
}

function pixels(width, height, pixel) {
  return Array.from({ length: width * height }, () => pixel).flat();
}

function target(id, access = 'write') {
  return textureResource(
    id,
    'render_target',
    access,
    'rgba8unorm',
    parameter('width'),
    parameter('height')
  );
}

function result(family, variant, objective, package_, contract, context, resourceId, expected) {
  return taskResult(
    family,
    variant,
    objective,
    package_,
    contract,
    context,
    { kind: 'rgba8_exact', resourceId, expected }
  );
}

function computeToRaster(family, variant) {
  const { width, height } = shape(variant);
  const pixel = variant % 2 === 0 ? [40, 180, 220, 255] : [220, 180, 40, 255];
  const resources = [
    bufferResource('positions', 'storage_buffer', 'read_write', literal(24)),
    bufferResource('draw-config', 'uniform_buffer', 'read', literal(16)),
    target('color'),
  ];
  const computeWgsl = `
@group(0) @binding(0) var<storage, read_write> positions: array<vec2<f32>>;
@compute @workgroup_size(3, 1, 1)
fn compute_main(@builtin(global_invocation_id) global_id: vec3<u32>) {
  let triangle = array<vec2<f32>, 3>(
    vec2<f32>(-1.0, -1.0), vec2<f32>(3.0, -1.0), vec2<f32>(-1.0, 3.0)
  );
  if (global_id.x < 3u) { positions[global_id.x] = triangle[global_id.x]; }
}`.trim();
  const renderWgsl = `
struct DrawConfig { color: vec4<f32> }
@group(0) @binding(0) var<storage, read> positions: array<vec2<f32>>;
@group(0) @binding(1) var<uniform> draw_config: DrawConfig;
@vertex
fn vertex_main(@builtin(vertex_index) vertex_index: u32) -> @builtin(position) vec4<f32> {
  return vec4<f32>(positions[vertex_index], 0.0, 1.0);
}
@fragment
fn fragment_main() -> @location(0) vec4<f32> { return draw_config.color; }
`.trim();
  const package_ = packageValue(
    [
      { id: 'prepare-module', wgsl: computeWgsl },
      { id: 'draw-module', wgsl: renderWgsl },
    ],
    resources,
    [
      computePass('prepare-module', [binding(0, 0, 'positions', 'positions')], {
        x: literal(1), y: literal(1), z: literal(1),
      }),
      renderPass({
        id: 'draw-pass',
        moduleId: 'draw-module',
        bindings: [
          binding(0, 0, 'positions', 'positions'),
          binding(0, 1, 'draw-config', 'draw_config'),
        ],
      }),
    ],
    ['color']
  );
  return result(
    family,
    variant,
    'Generate triangle positions in a compute pass, consume the same storage buffer in a render pass, and shade the complete target.',
    package_,
    contractFor(resources, ['width', 'height'], ['compute', 'render']),
    {
      parameters: { width, height },
      overrides: {},
      resources: {
        positions: { initialization: 'zero' },
        'draw-config': {
          initialization: 'bytes',
          bytes: bytesFromFloat32(pixel.map((value) => value / 255)),
        },
        color: { initialization: 'zero' },
      },
    },
    'color',
    pixels(width, height, pixel)
  );
}

function offscreenPostprocess(family, variant) {
  const { width, height } = shape(variant);
  const pixel = variant % 2 === 0 ? [72, 136, 200, 255] : [200, 136, 72, 255];
  const resources = [
    bufferResource('scene', 'uniform_buffer', 'read', literal(16)),
    target('offscreen', 'read_write'),
    samplerResource('postprocess-sampler', 'nearest'),
    target('color'),
  ];
  const sceneWgsl = `
struct Scene { color: vec4<f32> }
@group(0) @binding(0) var<uniform> scene: Scene;
@vertex
fn vertex_main(@builtin(vertex_index) vertex_index: u32) -> @builtin(position) vec4<f32> {
  let positions = array<vec2<f32>, 3>(
    vec2<f32>(-1.0, -1.0), vec2<f32>(3.0, -1.0), vec2<f32>(-1.0, 3.0)
  );
  return vec4<f32>(positions[vertex_index], 0.0, 1.0);
}
@fragment
fn fragment_main() -> @location(0) vec4<f32> { return scene.color; }
`.trim();
  const postWgsl = `
struct VertexOutput { @builtin(position) position: vec4<f32>, @location(0) uv: vec2<f32> }
@group(0) @binding(0) var offscreen: texture_2d<f32>;
@group(0) @binding(1) var postprocess_sampler: sampler;
@vertex
fn vertex_main(@builtin(vertex_index) vertex_index: u32) -> VertexOutput {
  let positions = array<vec2<f32>, 3>(
    vec2<f32>(-1.0, -1.0), vec2<f32>(3.0, -1.0), vec2<f32>(-1.0, 3.0)
  );
  let position = positions[vertex_index];
  var output: VertexOutput;
  output.position = vec4<f32>(position, 0.0, 1.0);
  output.uv = position * vec2<f32>(0.5, -0.5) + vec2<f32>(0.5);
  return output;
}
@fragment
fn fragment_main(input: VertexOutput) -> @location(0) vec4<f32> {
  return textureSample(offscreen, postprocess_sampler, input.uv);
}`.trim();
  const firstPass = renderPass({
    id: 'offscreen-pass',
    moduleId: 'scene-module',
    bindings: [binding(0, 0, 'scene', 'scene')],
    targetId: 'offscreen',
  });
  const secondPass = renderPass({
    id: 'postprocess-pass',
    moduleId: 'postprocess-module',
    bindings: [
      binding(0, 0, 'offscreen', 'offscreen'),
      binding(0, 1, 'postprocess-sampler', 'postprocess_sampler'),
    ],
  });
  const package_ = packageValue(
    [
      { id: 'scene-module', wgsl: sceneWgsl },
      { id: 'postprocess-module', wgsl: postWgsl },
    ],
    resources,
    [firstPass, secondPass],
    ['color']
  );
  return result(
    family,
    variant,
    'Render a host-colored offscreen target, then sample it in a separate full-screen postprocess pass.',
    package_,
    contractFor(resources, ['width', 'height'], ['render']),
    {
      parameters: { width, height },
      overrides: {},
      resources: {
        scene: { initialization: 'bytes', bytes: bytesFromFloat32(pixel.map((value) => value / 255)) },
        offscreen: { initialization: 'zero' },
        'postprocess-sampler': { initialization: 'descriptor' },
        color: { initialization: 'zero' },
      },
    },
    'color',
    pixels(width, height, pixel)
  );
}

function simulationVisualization(family, variant) {
  const { width, height } = shape(variant);
  const pixel = variant % 2 === 0 ? [96, 224, 160, 255] : [224, 96, 160, 255];
  const resources = [
    bufferResource('simulation-state', 'storage_buffer', 'read_write', literal(24)),
    bufferResource('visual-config', 'uniform_buffer', 'read', literal(16)),
    target('color'),
  ];
  const computeWgsl = `
@group(0) @binding(0) var<storage, read_write> simulation_state: array<vec2<f32>>;
@compute @workgroup_size(3, 1, 1)
fn compute_main(@builtin(global_invocation_id) global_id: vec3<u32>) {
  let positions = array<vec2<f32>, 3>(
    vec2<f32>(-1.0, -1.0), vec2<f32>(3.0, -1.0), vec2<f32>(-1.0, 3.0)
  );
  if (global_id.x < 3u) { simulation_state[global_id.x] = positions[global_id.x]; }
}`.trim();
  const renderWgsl = `
struct VisualConfig { color: vec4<f32> }
@group(0) @binding(0) var<storage, read> simulation_state: array<vec2<f32>>;
@group(0) @binding(1) var<uniform> visual_config: VisualConfig;
@vertex
fn vertex_main(
  @builtin(vertex_index) vertex_index: u32,
  @builtin(instance_index) instance_index: u32,
) -> @builtin(position) vec4<f32> {
  return vec4<f32>(simulation_state[vertex_index] + vec2<f32>(f32(instance_index) * 0.0), 0.0, 1.0);
}
@fragment
fn fragment_main() -> @location(0) vec4<f32> { return visual_config.color; }
`.trim();
  const package_ = packageValue(
    [
      { id: 'simulate-module', wgsl: computeWgsl },
      { id: 'visualize-module', wgsl: renderWgsl },
    ],
    resources,
    [
      computePass('simulate-module', [binding(0, 0, 'simulation-state', 'simulation_state')], {
        x: literal(1), y: literal(1), z: literal(1),
      }),
      renderPass({
        id: 'visualize-pass',
        moduleId: 'visualize-module',
        bindings: [
          binding(0, 0, 'simulation-state', 'simulation_state'),
          binding(0, 1, 'visual-config', 'visual_config'),
        ],
        draw: directDraw(literal(3), parameter('instanceCount')),
      }),
    ],
    ['color']
  );
  return result(
    family,
    variant,
    'Advance deterministic simulation state in compute and render it through a separate instanced visualization pass.',
    package_,
    contractFor(resources, ['width', 'height', 'instanceCount'], ['compute', 'render']),
    {
      parameters: { width, height, instanceCount: variant % 2 === 0 ? 1 : 2 },
      overrides: {},
      resources: {
        'simulation-state': { initialization: 'zero' },
        'visual-config': { initialization: 'bytes', bytes: bytesFromFloat32(pixel.map((value) => value / 255)) },
        color: { initialization: 'zero' },
      },
    },
    'color',
    pixels(width, height, pixel)
  );
}

function pingPongVisualization(family, variant) {
  const { width, height } = shape(variant);
  const pixel = variant % 2 === 0 ? [144, 72, 216, 255] : [72, 216, 144, 255];
  const input = pixels(width, height, pixel);
  const resources = [
    textureResource('state-a', 'sampled_texture', 'read', 'rgba8unorm', parameter('width'), parameter('height')),
    textureResource('state-b', 'storage_texture', 'read_write', 'rgba8unorm', parameter('width'), parameter('height')),
    samplerResource('state-sampler', 'nearest'),
    target('color'),
  ];
  const computeWgsl = `
override WORKGROUP_SIZE: u32 = 2u;
@group(0) @binding(0) var state_a: texture_2d<f32>;
@group(0) @binding(1) var state_b: texture_storage_2d<rgba8unorm, write>;
@compute @workgroup_size(WORKGROUP_SIZE, WORKGROUP_SIZE, 1)
fn compute_main(@builtin(global_invocation_id) global_id: vec3<u32>) {
  let size = textureDimensions(state_b);
  if (any(global_id.xy >= size)) { return; }
  textureStore(state_b, global_id.xy, textureLoad(state_a, vec2<i32>(global_id.xy), 0));
}`.trim();
  const renderWgsl = `
struct VertexOutput { @builtin(position) position: vec4<f32>, @location(0) uv: vec2<f32> }
@group(0) @binding(0) var state_b: texture_2d<f32>;
@group(0) @binding(1) var state_sampler: sampler;
@vertex
fn vertex_main(@builtin(vertex_index) vertex_index: u32) -> VertexOutput {
  let positions = array<vec2<f32>, 3>(
    vec2<f32>(-1.0, -1.0), vec2<f32>(3.0, -1.0), vec2<f32>(-1.0, 3.0)
  );
  let position = positions[vertex_index];
  var output: VertexOutput;
  output.position = vec4<f32>(position, 0.0, 1.0);
  output.uv = position * vec2<f32>(0.5, -0.5) + vec2<f32>(0.5);
  return output;
}
@fragment
fn fragment_main(input: VertexOutput) -> @location(0) vec4<f32> {
  return textureSample(state_b, state_sampler, input.uv);
}`.trim();
  const package_ = packageValue(
    [
      { id: 'ping-module', wgsl: computeWgsl },
      { id: 'visual-module', wgsl: renderWgsl },
    ],
    resources,
    [
      computePass('ping-module', [
        binding(0, 0, 'state-a', 'state_a'),
        binding(0, 1, 'state-b', 'state_b'),
      ], {
        x: operation('ceil_div', parameter('width'), override('WORKGROUP_SIZE')),
        y: operation('ceil_div', parameter('height'), override('WORKGROUP_SIZE')),
        z: literal(1),
      }, [{ name: 'WORKGROUP_SIZE', value: override('WORKGROUP_SIZE') }]),
      renderPass({
        id: 'visual-pass',
        moduleId: 'visual-module',
        bindings: [
          binding(0, 0, 'state-b', 'state_b'),
          binding(0, 1, 'state-sampler', 'state_sampler'),
        ],
      }),
    ],
    ['color']
  );
  return result(
    family,
    variant,
    'Write the next state texture in compute, then sample that exact texture in a visualization pass.',
    package_,
    contractFor(resources, ['width', 'height'], ['compute', 'render']),
    {
      parameters: { width, height },
      overrides: { WORKGROUP_SIZE: 2 },
      resources: {
        'state-a': { initialization: 'bytes', bytes: input },
        'state-b': { initialization: 'zero' },
        'state-sampler': { initialization: 'descriptor' },
        color: { initialization: 'zero' },
      },
    },
    'color',
    input
  );
}

export const WGSL_WRITER_V3_MULTIPASS_FAMILY_BUILDERS = Object.freeze({
  'compute-to-raster': computeToRaster,
  'offscreen-postprocess': offscreenPostprocess,
  'simulation-visualization': simulationVisualization,
  'ping-pong-visualization': pingPongVisualization,
});

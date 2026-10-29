import {
  binding,
  bufferResource,
  bytesFromFloat32,
  bytesFromUint32,
  contractFor,
  directDraw,
  literal,
  packageValue,
  parameter,
  renderPass,
  samplerResource,
  taskResult,
  textureResource,
} from './wgsl-writer-v3-family-builders.js';

function renderShape(variant) {
  return variant % 2 === 0
    ? { width: 3, height: 2 }
    : { width: 4, height: 3 };
}

function uniformPixels(width, height, pixel) {
  return Array.from({ length: width * height }, () => pixel).flat();
}

function targetResource(id = 'color', access = 'write') {
  return textureResource(
    id,
    'render_target',
    access,
    'rgba8unorm',
    parameter('width'),
    parameter('height')
  );
}

function commonContext(width, height, resources) {
  return {
    parameters: { width, height },
    overrides: {},
    resources,
  };
}

function exactTask(family, variant, objective, package_, contract, context, pixel) {
  return taskResult(
    family,
    variant,
    objective,
    package_,
    contract,
    context,
    {
      kind: 'rgba8_exact',
      resourceId: 'color',
      expected: uniformPixels(context.parameters.width, context.parameters.height, pixel),
    }
  );
}

function proceduralRaster(family, variant) {
  const { width, height } = renderShape(variant);
  const pixel = variant % 2 === 0 ? [64, 128, 191, 255] : [32, 160, 96, 255];
  const color = pixel.map((value) => value / 255);
  const resources = [
    bufferResource('scene', 'uniform_buffer', 'read', literal(16)),
    targetResource(),
  ];
  const wgsl = `
struct Scene { tint: vec4<f32> }
@group(0) @binding(0) var<uniform> scene: Scene;

@vertex
fn vertex_main(@builtin(vertex_index) vertex_index: u32) -> @builtin(position) vec4<f32> {
  let positions = array<vec2<f32>, 3>(
    vec2<f32>(-1.0, -1.0),
    vec2<f32>(3.0, -1.0),
    vec2<f32>(-1.0, 3.0)
  );
  return vec4<f32>(positions[vertex_index], 0.0, 1.0);
}

@fragment
fn fragment_main(@builtin(position) fragment_position: vec4<f32>) -> @location(0) vec4<f32> {
  let checker = u32(fragment_position.x + fragment_position.y) & 0u;
  return scene.tint + vec4<f32>(f32(checker));
}`.trim();
  const package_ = packageValue(
    [{ id: 'procedural-module', wgsl }],
    resources,
    [renderPass({
      moduleId: 'procedural-module',
      bindings: [binding(0, 0, 'scene', 'scene')],
    })],
    ['color']
  );
  return exactTask(
    family,
    variant,
    'Rasterize a viewport-covering procedural triangle and shade every fragment with the host-provided tint.',
    package_,
    contractFor(resources, ['width', 'height'], ['render']),
    commonContext(width, height, {
      scene: { initialization: 'bytes', bytes: bytesFromFloat32(color) },
      color: { initialization: 'zero' },
    }),
    pixel
  );
}

function indexedVertexColor(family, variant) {
  const { width, height } = renderShape(variant);
  const pixel = variant % 2 === 0 ? [204, 51, 102, 255] : [51, 178, 230, 255];
  const color = pixel.map((value) => value / 255);
  const positions = variant % 2 === 0
    ? [[-1, -1], [3, -1], [-1, 3]]
    : [[-1, -1], [1, -1], [-1, 1], [-1, 1], [1, -1], [1, 1]];
  const vertices = positions.flatMap((position) => [...position, ...color]);
  const indices = positions.map((_, index) => index);
  const resources = [
    bufferResource('vertices', 'vertex_buffer', 'read', parameter('vertexBytes'), 'host', {
      arrayStride: 24,
      stepMode: 'vertex',
      attributes: [
        { shaderLocation: 0, offset: 0, format: 'float32x2' },
        { shaderLocation: 1, offset: 8, format: 'float32x4' },
      ],
    }),
    bufferResource('indices', 'index_buffer', 'read', parameter('indexBytes'), 'host', {
      indexFormat: 'uint32',
    }),
    bufferResource('transform', 'uniform_buffer', 'read', literal(16)),
    targetResource(),
  ];
  const wgsl = `
struct Transform { scale: vec2<f32>, offset: vec2<f32> }
struct VertexOutput { @builtin(position) position: vec4<f32>, @location(0) color: vec4<f32> }
@group(0) @binding(0) var<uniform> transform: Transform;

@vertex
fn vertex_main(
  @location(0) position: vec2<f32>,
  @location(1) color: vec4<f32>,
) -> VertexOutput {
  var output: VertexOutput;
  output.position = vec4<f32>(position * transform.scale + transform.offset, 0.0, 1.0);
  output.color = color;
  return output;
}

@fragment
fn fragment_main(input: VertexOutput) -> @location(0) vec4<f32> {
  return input.color;
}`.trim();
  const package_ = packageValue(
    [{ id: 'indexed-color-module', wgsl }],
    resources,
    [renderPass({
      moduleId: 'indexed-color-module',
      bindings: [binding(0, 0, 'transform', 'transform')],
      vertexBuffers: [{ slot: 0, resourceId: 'vertices' }],
      indexBuffer: { resourceId: 'indices' },
      draw: {
        kind: 'indexed',
        indexCount: parameter('indexCount'),
        instanceCount: literal(1),
        firstIndex: literal(0),
        baseVertex: literal(0),
        firstInstance: literal(0),
      },
    })],
    ['color']
  );
  const context = commonContext(width, height, {
    vertices: { initialization: 'bytes', bytes: bytesFromFloat32(vertices) },
    indices: { initialization: 'bytes', bytes: bytesFromUint32(indices) },
    transform: { initialization: 'bytes', bytes: bytesFromFloat32([1, 1, 0, 0]) },
    color: { initialization: 'zero' },
  });
  Object.assign(context.parameters, {
    vertexBytes: vertices.length * 4,
    indexBytes: indices.length * 4,
    indexCount: indices.length,
  });
  return exactTask(
    family,
    variant,
    'Render an explicitly laid out indexed mesh, transform its positions, and interpolate its vertex color.',
    package_,
    contractFor(resources, ['width', 'height', 'vertexBytes', 'indexBytes', 'indexCount'], ['render']),
    context,
    pixel
  );
}

function texturedSprite(family, variant) {
  const { width, height } = renderShape(variant);
  const pixel = variant % 2 === 0 ? [80, 144, 224, 255] : [192, 96, 48, 255];
  const textureBytes = uniformPixels(2, 2, pixel);
  const resources = [
    textureResource('sprite-texture', 'sampled_texture', 'read', 'rgba8unorm', literal(2), literal(2)),
    samplerResource('sprite-sampler', 'nearest'),
    bufferResource('sprite-config', 'uniform_buffer', 'read', literal(16)),
    targetResource(),
  ];
  const wgsl = `
struct SpriteConfig { tint: vec4<f32> }
struct VertexOutput { @builtin(position) position: vec4<f32>, @location(0) uv: vec2<f32> }
@group(0) @binding(0) var sprite_texture: texture_2d<f32>;
@group(0) @binding(1) var sprite_sampler: sampler;
@group(0) @binding(2) var<uniform> sprite_config: SpriteConfig;

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
  let gradient_use = dpdx(input.uv.x) * 0.0 + dpdy(input.uv.y) * 0.0;
  return textureSample(sprite_texture, sprite_sampler, input.uv) * sprite_config.tint
    + vec4<f32>(gradient_use);
}`.trim();
  const package_ = packageValue(
    [{ id: 'sprite-module', wgsl }],
    resources,
    [renderPass({
      moduleId: 'sprite-module',
      bindings: [
        binding(0, 0, 'sprite-texture', 'sprite_texture'),
        binding(0, 1, 'sprite-sampler', 'sprite_sampler'),
        binding(0, 2, 'sprite-config', 'sprite_config'),
      ],
    })],
    ['color']
  );
  return exactTask(
    family,
    variant,
    'Render a sampled sprite with explicit coordinates, derivative use, nearest filtering, and a uniform tint.',
    package_,
    contractFor(resources, ['width', 'height'], ['render']),
    commonContext(width, height, {
      'sprite-texture': { initialization: 'bytes', bytes: textureBytes },
      'sprite-sampler': { initialization: 'descriptor' },
      'sprite-config': { initialization: 'bytes', bytes: bytesFromFloat32([1, 1, 1, 1]) },
      color: { initialization: 'zero' },
    }),
    pixel
  );
}

function instancedGlyphs(family, variant) {
  const { width, height } = renderShape(variant);
  const pixel = variant % 2 === 0 ? [120, 220, 80, 255] : [220, 120, 200, 255];
  const positions = variant % 2 === 0
    ? [-1, -1, 3, -1, -1, 3]
    : [-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1];
  const vertexCount = positions.length / 2;
  const resources = [
    bufferResource('glyph-vertices', 'vertex_buffer', 'read', parameter('vertexBytes'), 'host', {
      arrayStride: 8,
      stepMode: 'vertex',
      attributes: [{ shaderLocation: 0, offset: 0, format: 'float32x2' }],
    }),
    bufferResource('instances', 'storage_buffer', 'read', literal(16)),
    bufferResource('glyph-config', 'uniform_buffer', 'read', literal(32)),
    targetResource(),
  ];
  const wgsl = `
struct GlyphConfig { scale: vec2<f32>, reserved: vec2<f32>, color: vec4<f32> }
@group(0) @binding(0) var<storage, read> instance_offsets: array<vec2<f32>>;
@group(0) @binding(1) var<uniform> glyph_config: GlyphConfig;

@vertex
fn vertex_main(
  @location(0) position: vec2<f32>,
  @builtin(instance_index) instance_index: u32,
) -> @builtin(position) vec4<f32> {
  return vec4<f32>(
    position * glyph_config.scale + instance_offsets[instance_index],
    0.0,
    1.0
  );
}

@fragment
fn fragment_main() -> @location(0) vec4<f32> { return glyph_config.color; }
`.trim();
  const package_ = packageValue(
    [{ id: 'glyph-module', wgsl }],
    resources,
    [renderPass({
      moduleId: 'glyph-module',
      bindings: [
        binding(0, 0, 'instances', 'instance_offsets'),
        binding(0, 1, 'glyph-config', 'glyph_config'),
      ],
      vertexBuffers: [{ slot: 0, resourceId: 'glyph-vertices' }],
      draw: directDraw(parameter('vertexCount'), parameter('instanceCount')),
    })],
    ['color']
  );
  const config = [...bytesFromFloat32([1, 1, 0, 0]), ...bytesFromFloat32(pixel.map((value) => value / 255))];
  const context = commonContext(width, height, {
    'glyph-vertices': { initialization: 'bytes', bytes: bytesFromFloat32(positions) },
    instances: { initialization: 'bytes', bytes: bytesFromFloat32([0, 0, 0, 0]) },
    'glyph-config': { initialization: 'bytes', bytes: config },
    color: { initialization: 'zero' },
  });
  Object.assign(context.parameters, {
    vertexBytes: positions.length * 4,
    vertexCount,
    instanceCount: variant % 2 === 0 ? 1 : 2,
  });
  return exactTask(
    family,
    variant,
    'Draw viewport-covering glyph geometry through a vertex layout and per-instance storage offsets.',
    package_,
    contractFor(resources, [
      'width',
      'height',
      'vertexBytes',
      'vertexCount',
      'instanceCount',
    ], ['render']),
    context,
    pixel
  );
}

function sampledMeshTransform(family, variant) {
  const { width, height } = renderShape(variant);
  const pixel = variant % 2 === 0 ? [176, 112, 48, 255] : [48, 112, 176, 255];
  const positions = variant % 2 === 0
    ? [-1, -1, 0, 0, 3, -1, 1, 0, -1, 3, 0, 1]
    : [-1, -1, 0, 0, 1, -1, 1, 0, -1, 1, 0, 1, -1, 1, 0, 1, 1, -1, 1, 0, 1, 1, 1, 1];
  const indexCount = positions.length / 4;
  const resources = [
    bufferResource('mesh-vertices', 'vertex_buffer', 'read', parameter('vertexBytes'), 'host', {
      arrayStride: 16,
      stepMode: 'vertex',
      attributes: [
        { shaderLocation: 0, offset: 0, format: 'float32x2' },
        { shaderLocation: 1, offset: 8, format: 'float32x2' },
      ],
    }),
    bufferResource('mesh-indices', 'index_buffer', 'read', parameter('indexBytes'), 'host', { indexFormat: 'uint32' }),
    bufferResource('mesh-transform', 'uniform_buffer', 'read', literal(16)),
    textureResource('material-texture', 'sampled_texture', 'read', 'rgba8unorm', literal(2), literal(2)),
    samplerResource('material-sampler', 'nearest'),
    targetResource(),
  ];
  const wgsl = `
struct MeshTransform { scale: vec2<f32>, offset: vec2<f32> }
struct VertexOutput { @builtin(position) position: vec4<f32>, @location(0) uv: vec2<f32> }
@group(0) @binding(0) var<uniform> mesh_transform: MeshTransform;
@group(0) @binding(1) var material_texture: texture_2d<f32>;
@group(0) @binding(2) var material_sampler: sampler;

@vertex
fn vertex_main(@location(0) position: vec2<f32>, @location(1) uv: vec2<f32>) -> VertexOutput {
  var output: VertexOutput;
  output.position = vec4<f32>(position * mesh_transform.scale + mesh_transform.offset, 0.0, 1.0);
  output.uv = uv;
  return output;
}
@fragment
fn fragment_main(input: VertexOutput) -> @location(0) vec4<f32> {
  return textureSample(material_texture, material_sampler, input.uv);
}`.trim();
  const package_ = packageValue(
    [{ id: 'sampled-mesh-module', wgsl }],
    resources,
    [renderPass({
      moduleId: 'sampled-mesh-module',
      bindings: [
        binding(0, 0, 'mesh-transform', 'mesh_transform'),
        binding(0, 1, 'material-texture', 'material_texture'),
        binding(0, 2, 'material-sampler', 'material_sampler'),
      ],
      vertexBuffers: [{ slot: 0, resourceId: 'mesh-vertices' }],
      indexBuffer: { resourceId: 'mesh-indices' },
      draw: {
        kind: 'indexed',
        indexCount: parameter('indexCount'),
        instanceCount: literal(1),
        firstIndex: literal(0),
        baseVertex: literal(0),
        firstInstance: literal(0),
      },
    })],
    ['color']
  );
  return exactTask(
    family,
    variant,
    'Transform an indexed mesh with an explicit vertex layout and shade it from sampled material data.',
    package_,
    contractFor(resources, ['width', 'height', 'vertexBytes', 'indexBytes', 'indexCount'], ['render']),
    (() => {
      const context = commonContext(width, height, {
      'mesh-vertices': { initialization: 'bytes', bytes: bytesFromFloat32(positions) },
      'mesh-indices': { initialization: 'bytes', bytes: bytesFromUint32(Array.from({ length: indexCount }, (_, index) => index)) },
      'mesh-transform': { initialization: 'bytes', bytes: bytesFromFloat32([1, 1, 0, 0]) },
      'material-texture': { initialization: 'bytes', bytes: uniformPixels(2, 2, pixel) },
      'material-sampler': { initialization: 'descriptor' },
      color: { initialization: 'zero' },
      });
      Object.assign(context.parameters, {
        vertexBytes: positions.length * 4,
        indexBytes: indexCount * 4,
        indexCount,
      });
      return context;
    })(),
    pixel
  );
}

function indexedShadedMesh(family, variant) {
  const { width, height } = renderShape(variant);
  const pixel = variant % 2 === 0 ? [153, 102, 204, 255] : [102, 204, 153, 255];
  const baseColor = pixel.slice(0, 3).map((value) => value / 255);
  const positions = variant % 2 === 0
    ? [[-1, -1], [3, -1], [-1, 3]]
    : [[-1, -1], [1, -1], [-1, 1], [-1, 1], [1, -1], [1, 1]];
  const vertices = positions.flatMap((position) => [...position, 0, 0, 1]);
  const indexCount = positions.length;
  const resources = [
    bufferResource('shaded-vertices', 'vertex_buffer', 'read', parameter('vertexBytes'), 'host', {
      arrayStride: 20,
      stepMode: 'vertex',
      attributes: [
        { shaderLocation: 0, offset: 0, format: 'float32x2' },
        { shaderLocation: 1, offset: 8, format: 'float32x3' },
      ],
    }),
    bufferResource('shaded-indices', 'index_buffer', 'read', parameter('indexBytes'), 'host', { indexFormat: 'uint32' }),
    bufferResource('lighting', 'uniform_buffer', 'read', literal(32)),
    targetResource(),
  ];
  const wgsl = `
struct Lighting { light_direction: vec3<f32>, reserved: f32, base_color: vec4<f32> }
struct VertexOutput { @builtin(position) position: vec4<f32>, @location(0) normal: vec3<f32> }
@group(0) @binding(0) var<uniform> lighting: Lighting;

@vertex
fn vertex_main(@location(0) position: vec2<f32>, @location(1) normal: vec3<f32>) -> VertexOutput {
  var output: VertexOutput;
  output.position = vec4<f32>(position, 0.0, 1.0);
  output.normal = normal;
  return output;
}
@fragment
fn fragment_main(input: VertexOutput) -> @location(0) vec4<f32> {
  let intensity = max(dot(normalize(input.normal), normalize(lighting.light_direction)), 0.0);
  return vec4<f32>(lighting.base_color.rgb * intensity, lighting.base_color.a);
}`.trim();
  const package_ = packageValue(
    [{ id: 'shaded-mesh-module', wgsl }],
    resources,
    [renderPass({
      moduleId: 'shaded-mesh-module',
      bindings: [binding(0, 0, 'lighting', 'lighting')],
      vertexBuffers: [{ slot: 0, resourceId: 'shaded-vertices' }],
      indexBuffer: { resourceId: 'shaded-indices' },
      draw: {
        kind: 'indexed',
        indexCount: parameter('indexCount'),
        instanceCount: literal(1),
        firstIndex: literal(0),
        baseVertex: literal(0),
        firstInstance: literal(0),
      },
    })],
    ['color']
  );
  const lighting = [...bytesFromFloat32([0, 0, 1, 0]), ...bytesFromFloat32([...baseColor, 1])];
  return exactTask(
    family,
    variant,
    'Render an indexed mesh with interpolated normals and deterministic directional lighting.',
    package_,
    contractFor(resources, ['width', 'height', 'vertexBytes', 'indexBytes', 'indexCount'], ['render']),
    (() => {
      const context = commonContext(width, height, {
      'shaded-vertices': { initialization: 'bytes', bytes: bytesFromFloat32(vertices) },
      'shaded-indices': { initialization: 'bytes', bytes: bytesFromUint32(Array.from({ length: indexCount }, (_, index) => index)) },
      lighting: { initialization: 'bytes', bytes: lighting },
      color: { initialization: 'zero' },
      });
      Object.assign(context.parameters, {
        vertexBytes: vertices.length * 4,
        indexBytes: indexCount * 4,
        indexCount,
      });
      return context;
    })(),
    pixel
  );
}

export const WGSL_WRITER_V3_RENDER_FAMILY_BUILDERS = Object.freeze({
  'procedural-raster': proceduralRaster,
  'indexed-vertex-color': indexedVertexColor,
  'textured-sprite': texturedSprite,
  'instanced-glyphs': instancedGlyphs,
  'sampled-mesh-transform': sampledMeshTransform,
  'indexed-shaded-mesh': indexedShadedMesh,
});

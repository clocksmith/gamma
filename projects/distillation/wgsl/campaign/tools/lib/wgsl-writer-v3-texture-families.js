import {
  binding,
  bufferResource,
  bytesFromUint32,
  computePass,
  contractFor,
  literal,
  operation,
  override,
  packageValue,
  parameter,
  samplerResource,
  taskResult,
  textureResource,
} from './wgsl-writer-v3-family-builders.js';

function textureShape(variant) {
  return variant % 2 === 0
    ? { width: 2, height: 2, workgroupSize: 2 }
    : { width: 3, height: 2, workgroupSize: 1 };
}

function patternedPixels(width, height, variant) {
  const bytes = [];
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      bytes.push(
        (x * 67 + variant * 19) % 256,
        (y * 103 + variant * 11) % 256,
        ((x + y) * 47 + 31) % 256,
        255
      );
    }
  }
  return bytes;
}

function textureCopy(family, variant) {
  const { width, height, workgroupSize } = textureShape(variant);
  const pixels = patternedPixels(width, height, variant);
  const resources = [
    textureResource(
      'source-texture',
      'sampled_texture',
      'read',
      'rgba8unorm',
      parameter('width'),
      parameter('height')
    ),
    samplerResource('source-sampler', 'nearest'),
    textureResource(
      'result-texture',
      'storage_texture',
      'write',
      'rgba8unorm',
      parameter('width'),
      parameter('height')
    ),
  ];
  const wgsl = `
override WORKGROUP_SIZE: u32 = 2u;

@group(0) @binding(0) var source_texture: texture_2d<f32>;
@group(0) @binding(1) var source_sampler: sampler;
@group(0) @binding(2) var result_texture: texture_storage_2d<rgba8unorm, write>;

@compute @workgroup_size(WORKGROUP_SIZE, WORKGROUP_SIZE, 1)
fn compute_main(@builtin(global_invocation_id) global_id: vec3<u32>) {
  let size = textureDimensions(result_texture);
  let coordinate = global_id.xy;
  if (any(coordinate >= size)) { return; }
  let uv = (vec2<f32>(coordinate) + vec2<f32>(0.5)) / vec2<f32>(size);
  let loaded = textureLoad(source_texture, vec2<i32>(coordinate), 0);
  let sampled = textureSampleLevel(source_texture, source_sampler, uv, 0.0);
  textureStore(result_texture, coordinate, sampled + loaded * 0.0);
}`.trim();
  const package_ = packageValue(
    [{ id: 'texture-filter-module', wgsl }],
    resources,
    [computePass('texture-filter-module', [
      binding(0, 0, 'source-texture', 'source_texture'),
      binding(0, 1, 'source-sampler', 'source_sampler'),
      binding(0, 2, 'result-texture', 'result_texture'),
    ], {
      x: operation('ceil_div', parameter('width'), override('WORKGROUP_SIZE')),
      y: operation('ceil_div', parameter('height'), override('WORKGROUP_SIZE')),
      z: literal(1),
    }, [{ name: 'WORKGROUP_SIZE', value: override('WORKGROUP_SIZE') }])],
    ['result-texture']
  );
  return taskResult(
    family,
    variant,
    'Copy an rgba8 image through an explicitly sampled texture into a storage texture with exact edge-safe dispatch.',
    package_,
    contractFor(resources, ['width', 'height'], ['compute']),
    {
      parameters: { width, height },
      overrides: { WORKGROUP_SIZE: workgroupSize },
      resources: {
        'source-texture': { initialization: 'bytes', bytes: pixels },
        'source-sampler': { initialization: 'descriptor' },
        'result-texture': { initialization: 'zero' },
      },
    },
    { kind: 'rgba8_exact', resourceId: 'result-texture', expected: pixels }
  );
}

function cellularStep(family, variant) {
  const { width, height, workgroupSize } = textureShape(variant);
  const pixels = patternedPixels(width, height, variant);
  const expected = [...pixels];
  for (let offset = 0; offset < expected.length; offset += 4) {
    expected[offset] = 255 - expected[offset];
  }
  const resources = [
    textureResource(
      'current-state',
      'sampled_texture',
      'read',
      'rgba8unorm',
      parameter('width'),
      parameter('height')
    ),
    textureResource(
      'next-state',
      'storage_texture',
      'write',
      'rgba8unorm',
      parameter('width'),
      parameter('height')
    ),
    bufferResource('grid-config', 'uniform_buffer', 'read', literal(16)),
  ];
  const wgsl = `
override WORKGROUP_SIZE: u32 = 2u;

struct GridConfig { width: u32, height: u32, reserved_0: u32, reserved_1: u32 }
@group(0) @binding(0) var current_state: texture_2d<f32>;
@group(0) @binding(1) var next_state: texture_storage_2d<rgba8unorm, write>;
@group(0) @binding(2) var<uniform> grid_config: GridConfig;

@compute @workgroup_size(WORKGROUP_SIZE, WORKGROUP_SIZE, 1)
fn compute_main(@builtin(global_invocation_id) global_id: vec3<u32>) {
  let coordinate = global_id.xy;
  if (coordinate.x >= grid_config.width || coordinate.y >= grid_config.height) { return; }
  let value = textureLoad(current_state, vec2<i32>(coordinate), 0);
  textureStore(next_state, coordinate, vec4<f32>(1.0 - value.r, value.gba));
}`.trim();
  const package_ = packageValue(
    [{ id: 'cellular-module', wgsl }],
    resources,
    [computePass('cellular-module', [
      binding(0, 0, 'current-state', 'current_state'),
      binding(0, 1, 'next-state', 'next_state'),
      binding(0, 2, 'grid-config', 'grid_config'),
    ], {
      x: operation('ceil_div', parameter('width'), override('WORKGROUP_SIZE')),
      y: operation('ceil_div', parameter('height'), override('WORKGROUP_SIZE')),
      z: literal(1),
    }, [{ name: 'WORKGROUP_SIZE', value: override('WORKGROUP_SIZE') }])],
    ['next-state']
  );
  return taskResult(
    family,
    variant,
    'Apply a deterministic cellular update that inverts the red channel and preserves the other channels at every bounded coordinate.',
    package_,
    contractFor(resources, ['width', 'height'], ['compute']),
    {
      parameters: { width, height },
      overrides: { WORKGROUP_SIZE: workgroupSize },
      resources: {
        'current-state': { initialization: 'bytes', bytes: pixels },
        'next-state': { initialization: 'zero' },
        'grid-config': {
          initialization: 'bytes',
          bytes: bytesFromUint32([width, height, 0, 0]),
        },
      },
    },
    { kind: 'rgba8_exact', resourceId: 'next-state', expected }
  );
}

function normalizedConvolution(family, variant) {
  const { width, height, workgroupSize } = textureShape(variant);
  const pixel = [64 + variant * 8, 96, 160, 255];
  const pixels = Array.from({ length: width * height }, () => pixel).flat();
  const resources = [
    textureResource('source-image', 'sampled_texture', 'read', 'rgba8unorm', parameter('width'), parameter('height')),
    samplerResource('image-sampler', 'nearest'),
    textureResource('filtered-image', 'storage_texture', 'write', 'rgba8unorm', parameter('width'), parameter('height')),
    bufferResource('filter-config', 'uniform_buffer', 'read', literal(16)),
  ];
  const wgsl = `
override WORKGROUP_SIZE: u32 = 2u;

struct FilterConfig { width: u32, height: u32, reserved_0: u32, reserved_1: u32 }
@group(0) @binding(0) var source_image: texture_2d<f32>;
@group(0) @binding(1) var image_sampler: sampler;
@group(0) @binding(2) var filtered_image: texture_storage_2d<rgba8unorm, write>;
@group(0) @binding(3) var<uniform> filter_config: FilterConfig;

@compute @workgroup_size(WORKGROUP_SIZE, WORKGROUP_SIZE, 1)
fn compute_main(@builtin(global_invocation_id) global_id: vec3<u32>) {
  let coordinate = global_id.xy;
  if (coordinate.x >= filter_config.width || coordinate.y >= filter_config.height) { return; }
  let size = vec2<f32>(vec2<u32>(filter_config.width, filter_config.height));
  let center = (vec2<f32>(coordinate) + vec2<f32>(0.5)) / size;
  let step = vec2<f32>(1.0 / size.x, 0.0);
  let exact_center = textureLoad(source_image, vec2<i32>(coordinate), 0);
  let filtered = (
    textureSampleLevel(source_image, image_sampler, center - step, 0.0)
    + textureSampleLevel(source_image, image_sampler, center, 0.0) * 2.0
    + textureSampleLevel(source_image, image_sampler, center + step, 0.0)
  ) * 0.25;
  textureStore(filtered_image, coordinate, filtered + exact_center * 0.0);
}`.trim();
  const package_ = packageValue(
    [{ id: 'convolution-module', wgsl }],
    resources,
    [computePass('convolution-module', [
      binding(0, 0, 'source-image', 'source_image'),
      binding(0, 1, 'image-sampler', 'image_sampler'),
      binding(0, 2, 'filtered-image', 'filtered_image'),
      binding(0, 3, 'filter-config', 'filter_config'),
    ], {
      x: operation('ceil_div', parameter('width'), override('WORKGROUP_SIZE')),
      y: operation('ceil_div', parameter('height'), override('WORKGROUP_SIZE')),
      z: literal(1),
    }, [{ name: 'WORKGROUP_SIZE', value: override('WORKGROUP_SIZE') }])],
    ['filtered-image']
  );
  return taskResult(
    family,
    variant,
    'Apply a normalized horizontal 1-2-1 convolution with clamp-to-edge sampling.',
    package_,
    contractFor(resources, ['width', 'height'], ['compute']),
    {
      parameters: { width, height },
      overrides: { WORKGROUP_SIZE: workgroupSize },
      resources: {
        'source-image': { initialization: 'bytes', bytes: pixels },
        'image-sampler': { initialization: 'descriptor' },
        'filtered-image': { initialization: 'zero' },
        'filter-config': { initialization: 'bytes', bytes: bytesFromUint32([width, height, 0, 0]) },
      },
    },
    { kind: 'rgba8_exact', resourceId: 'filtered-image', expected: pixels }
  );
}

function coordinateWarp(family, variant) {
  const { width, height, workgroupSize } = textureShape(variant);
  const pixels = patternedPixels(width, height, variant);
  const expected = [];
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const sourceOffset = (y * width + (width - 1 - x)) * 4;
      expected.push(...pixels.slice(sourceOffset, sourceOffset + 4));
    }
  }
  const resources = [
    textureResource('source-image', 'sampled_texture', 'read', 'rgba8unorm', parameter('width'), parameter('height')),
    samplerResource('warp-sampler', 'nearest'),
    textureResource('warped-image', 'storage_texture', 'write', 'rgba8unorm', parameter('width'), parameter('height')),
    bufferResource('warp-config', 'uniform_buffer', 'read', literal(16)),
  ];
  const wgsl = `
override WORKGROUP_SIZE: u32 = 2u;

struct WarpConfig { width: u32, height: u32, reserved_0: u32, reserved_1: u32 }
@group(0) @binding(0) var source_image: texture_2d<f32>;
@group(0) @binding(1) var warp_sampler: sampler;
@group(0) @binding(2) var warped_image: texture_storage_2d<rgba8unorm, write>;
@group(0) @binding(3) var<uniform> warp_config: WarpConfig;

@compute @workgroup_size(WORKGROUP_SIZE, WORKGROUP_SIZE, 1)
fn compute_main(@builtin(global_invocation_id) global_id: vec3<u32>) {
  let coordinate = global_id.xy;
  if (coordinate.x >= warp_config.width || coordinate.y >= warp_config.height) { return; }
  let source_coordinate = vec2<u32>(warp_config.width - 1u - coordinate.x, coordinate.y);
  let uv = (vec2<f32>(source_coordinate) + vec2<f32>(0.5))
    / vec2<f32>(vec2<u32>(warp_config.width, warp_config.height));
  textureStore(warped_image, coordinate, textureSampleLevel(source_image, warp_sampler, uv, 0.0));
}`.trim();
  const package_ = packageValue(
    [{ id: 'warp-module', wgsl }],
    resources,
    [computePass('warp-module', [
      binding(0, 0, 'source-image', 'source_image'),
      binding(0, 1, 'warp-sampler', 'warp_sampler'),
      binding(0, 2, 'warped-image', 'warped_image'),
      binding(0, 3, 'warp-config', 'warp_config'),
    ], {
      x: operation('ceil_div', parameter('width'), override('WORKGROUP_SIZE')),
      y: operation('ceil_div', parameter('height'), override('WORKGROUP_SIZE')),
      z: literal(1),
    }, [{ name: 'WORKGROUP_SIZE', value: override('WORKGROUP_SIZE') }])],
    ['warped-image']
  );
  return taskResult(
    family,
    variant,
    'Mirror an input image horizontally with explicit nearest sampling and an out-of-range dispatch guard.',
    package_,
    contractFor(resources, ['width', 'height'], ['compute']),
    {
      parameters: { width, height },
      overrides: { WORKGROUP_SIZE: workgroupSize },
      resources: {
        'source-image': { initialization: 'bytes', bytes: pixels },
        'warp-sampler': { initialization: 'descriptor' },
        'warped-image': { initialization: 'zero' },
        'warp-config': { initialization: 'bytes', bytes: bytesFromUint32([width, height, 0, 0]) },
      },
    },
    { kind: 'rgba8_exact', resourceId: 'warped-image', expected }
  );
}

export const WGSL_WRITER_V3_TEXTURE_FAMILY_BUILDERS = Object.freeze({
  'storage-texture-filter': textureCopy,
  'cellular-step': cellularStep,
  'normalized-convolution': normalizedConvolution,
  'coordinate-image-warp': coordinateWarp,
});

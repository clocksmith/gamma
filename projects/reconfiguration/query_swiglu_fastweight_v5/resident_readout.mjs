// Score the answer marker while its existing Doppler ffn_act buffer is available.
// Weights stay packed. Only the class scores need to leave the device.
const shader = `
struct Shape {
  width: u32, weightOffset: u32, classStride: u32, classes: u32,
  firstRow: u32, firstLayer: u32, halfInput: u32, unused: u32,
}
@group(0) @binding(0) var<storage, read> weights: array<u32>;
@group(0) @binding(1) var<storage, read> features: array<u32>;
@group(0) @binding(2) var<storage, read_write> scores: array<f32>;
@group(0) @binding(3) var<uniform> shape: Shape;
var<workgroup> sums: array<f32, 64>;
fn coefficient(i: u32) -> f32 {
  return unpack2x16float(weights[i / 2u])[i % 2u];
}
@compute @workgroup_size(64)
fn main(@builtin(workgroup_id) group: vec3<u32>, @builtin(local_invocation_index) lane: u32) {
  let base = group.x * shape.classStride;
  let inputBase = (group.y + shape.firstRow) * shape.width;
  var sum = 0.0;
  for (var i = lane; i < shape.width; i += 64u) {
    let j = inputBase + i;
    var value: f32;
    if (shape.halfInput == 1u) {
      value = unpack2x16float(features[j / 2u])[j % 2u];
    } else {
      value = bitcast<f32>(features[j]);
    }
    sum += value * coefficient(base + shape.weightOffset + i);
  }
  sums[lane] = sum;
  workgroupBarrier();
  for (var step = 32u; step > 0u; step /= 2u) {
    if (lane < step) { sums[lane] += sums[lane + step]; }
    workgroupBarrier();
  }
  if (lane == 0u) {
    let dst = group.y * shape.classes + group.x;
    if (shape.firstLayer == 1u) { scores[dst] = coefficient(base) + sums[0]; }
    else { scores[dst] += sums[0]; }
  }
}
`;

function check(condition, message) {
  if (!condition) throw new Error(message);
}

function uploadedBuffer(device, bytes, usage) {
  const size = Math.ceil(bytes.byteLength / 4) * 4;
  const buffer = device.createBuffer({ size, usage, mappedAtCreation: true });
  new Uint8Array(buffer.getMappedRange()).set(bytes);
  buffer.unmap();
  return buffer;
}

export async function createReadoutKernel(device) {
  return device.createComputePipelineAsync({ layout: 'auto', compute: {
    module: device.createShaderModule({ code: shader }), entryPoint: 'main'
  } });
}

// The caller supplies the pinned model and activation layout from the running engine.
export async function loadResidentReadout(device, pipeline, header, bytes, base) {
  check(header.schema === 'gamma.linear-classifier/v1' && header.dtype === 'f16'
    && header.endian === 'little' && header.layout === 'class-major intercept then layer features'
    && header.feature === 'bare answer marker MLP intermediate', 'Unsupported classifier layout');
  check(header.model === base.model && header.baseManifestSha256 === base.manifestSha256
    && /^[a-f0-9]{64}$/.test(base.manifestSha256), 'Classifier base model differs');
  check(Array.isArray(base.layers) && base.layers.length > 0
    && base.layers.every((layer, i) => Number.isInteger(layer) && layer >= 0
      && (i === 0 || layer > base.layers[i-1]))
    && base.layers.length === base.dimensions?.length
    && base.dimensions.every(n => Number.isSafeInteger(n) && n > 0)
    && JSON.stringify(base.layers) === JSON.stringify(header.layers)
    && JSON.stringify(base.dimensions) === JSON.stringify(header.dimensions), 'Classifier feature binding differs');
  const layers = [...base.layers], widths = [...base.dimensions];
  check(Array.isArray(header.codes) && header.codes.length > 1 && header.codes.every(c => typeof c === 'string' && c.length > 0)
    && new Set(header.codes).size === header.codes.length, 'Invalid classifier codes');
  const codes = Object.freeze([...header.codes]), stride = 1 + widths.reduce((sum, n) => sum + n, 0);
  check(bytes instanceof Uint8Array && bytes.length === codes.length * stride * 2, 'Invalid coefficient count');
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
  check(Array.from(digest, n => n.toString(16).padStart(2,'0')).join('') === header.sha256, 'Classifier coefficients differ');
  const weights = uploadedBuffer(device, bytes, GPUBufferUsage.STORAGE);
  let closed = false;
  return {
    codes, residentWeightBytes: weights.size,
    // Each decision owns its output. Record each capture immediately in the caller's ordered command stream.
    begin({ firstRow = 0, rows = 1 } = {}) {
      check(!closed && Number.isSafeInteger(firstRow) && firstRow >= 0
        && Number.isSafeInteger(rows) && rows > 0 && rows <= device.limits.maxComputeWorkgroupsPerDimension, 'Invalid decision range');
      const output = device.createBuffer({ size: rows * codes.length * 4, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC });
      const uniforms = [];
      let next = 0, offset = 1, disposed = false;
      return {
        record(encoder, layer, tensor) {
          check(!closed && !disposed && next < layers.length && layer === layers[next], 'Unexpected readout layer');
          const halfInput = tensor.dtype === 'f16';
          check(halfInput || tensor.dtype === 'f32', 'Unsupported activation type');
          const width = widths[next];
          const inputBytes = (firstRow + rows) * width * (halfInput ? 2 : 4);
          check(Number.isSafeInteger(inputBytes) && inputBytes <= tensor.buffer.size && tensor.width === width, 'Incomplete feature rows');
          const params = new Uint32Array([width, offset, stride, codes.length, firstRow, Number(next === 0), Number(halfInput), 0]);
          const uniform = uploadedBuffer(device, new Uint8Array(params.buffer), GPUBufferUsage.UNIFORM);
          uniforms.push(uniform);
          const entries = [weights, tensor.buffer, output, uniform].map((buffer, binding) => ({ binding, resource: { buffer } }));
          const pass = encoder.beginComputePass();
          pass.setPipeline(pipeline);
          pass.setBindGroup(0, device.createBindGroup({ layout: pipeline.getBindGroupLayout(0), entries }));
          pass.dispatchWorkgroups(codes.length, rows);
          pass.end();
          offset += width;
          next++;
        },
        copyScores(encoder, destination) {
          check(!disposed && !closed && next === layers.length, 'Missing readout layer');
          encoder.copyBufferToBuffer(output, 0, destination, 0, output.size);
        },
        // Call after the commands have been submitted, or when discarding this decision.
        destroy() { disposed = true; output.destroy(); for (const buffer of uniforms) buffer.destroy(); }
      };
    },
    destroy() { closed = true; weights.destroy(); }
  };
}

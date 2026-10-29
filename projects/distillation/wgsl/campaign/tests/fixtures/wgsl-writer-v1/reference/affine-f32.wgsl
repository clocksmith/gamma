override WORKGROUP_SIZE: u32 = 64u;

struct Params {
  length: u32,
  output_offset: u32,
  scale: f32,
  bias: f32,
}

@group(0) @binding(0) var<storage, read> input_values: array<f32>;
@group(0) @binding(1) var<storage, read_write> output_values: array<f32>;
@group(0) @binding(2) var<uniform> params: Params;

@compute @workgroup_size(WORKGROUP_SIZE)
fn main(@builtin(global_invocation_id) global_id: vec3<u32>) {
  let index = global_id.x;
  if (index >= params.length) {
    return;
  }
  output_values[params.output_offset + index] =
    input_values[index] * params.scale + params.bias;
}

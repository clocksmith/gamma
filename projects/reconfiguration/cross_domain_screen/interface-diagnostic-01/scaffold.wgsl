struct Params { length: u32, output_offset: u32, first: f32, second: f32, }
@group(0) @binding(0) var<storage, read> left_values: array<f32>;
@group(0) @binding(1) var<storage, read> right_values: array<f32>;
@group(0) @binding(2) var<storage, read_write> output_values: array<f32>;
@group(0) @binding(3) var<uniform> params: Params;
override WORKGROUP_SIZE: u32 = 32u;
@compute @workgroup_size(WORKGROUP_SIZE)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let i = gid.x;
  if (i >= params.length) { return; }
  let x = left_values[i];
  let y = right_values[i];
  output_values[params.output_offset + i] = 0.0; // REPLACE_EXPRESSION
}

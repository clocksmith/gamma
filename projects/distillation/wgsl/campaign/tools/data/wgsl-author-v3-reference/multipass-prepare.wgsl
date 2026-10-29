@group(0) @binding(0) var<storage, read_write> colorData: array<vec4<f32>>;

@compute @workgroup_size(1)
fn compute_main(@builtin(global_invocation_id) gid: vec3<u32>) {
  if (gid.x == 0u) {
    colorData[0] = vec4<f32>(0.2, 0.4, 0.6, 1.0);
  }
}

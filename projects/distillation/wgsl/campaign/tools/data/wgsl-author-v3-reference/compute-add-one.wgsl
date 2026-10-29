@group(0) @binding(0) var<storage, read> sourceValues: array<f32>;
@group(0) @binding(1) var<storage, read_write> resultValues: array<f32>;

@compute @workgroup_size(4)
fn compute_main(@builtin(global_invocation_id) gid: vec3<u32>) {
  if (gid.x < arrayLength(&resultValues)) {
    resultValues[gid.x] = sourceValues[gid.x] + 1.0;
  }
}

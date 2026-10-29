@group(0) @binding(0) var<storage, read> colorData: array<vec4<f32>>;

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
  return colorData[0];
}

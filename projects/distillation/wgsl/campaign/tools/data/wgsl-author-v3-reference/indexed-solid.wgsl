struct VertexOutput {
  @builtin(position) position: vec4<f32>,
};

@vertex
fn vertex_main(@location(0) position: vec2<f32>) -> VertexOutput {
  var output: VertexOutput;
  output.position = vec4<f32>(position, 0.0, 1.0);
  return output;
}

@fragment
fn fragment_main() -> @location(0) vec4<f32> {
  return vec4<f32>(0.0, 1.0, 0.0, 1.0);
}

const FEATURE_PATTERNS = Object.freeze({
  atomics: /\batomic(?:Add|Load|Store|Sub|Max|Min|And|Or|Xor|Exchange|CompareExchangeWeak)?\b/u,
  barriers: /\bworkgroupBarrier\s*\(/u,
  overrides: /\boverride\s+[A-Za-z_][A-Za-z0-9_]*\s*:/u,
  'workgroup-memory': /var\s*<\s*workgroup\s*>/u,
  'texture-load': /\btextureLoad\s*\(/u,
  'texture-store': /\btextureStore\s*\(/u,
  'texture-sampling': /\btextureSample(?:Level|Bias|Grad|Compare|CompareLevel)?\s*\(/u,
  derivatives: /\b(?:dpdx|dpdy|fwidth)(?:Coarse|Fine)?\s*\(/u,
  'instance-index': /@builtin\s*\(\s*instance_index\s*\)/u,
  'vertex-inputs': /@location\s*\(\s*\d+\s*\)\s+[A-Za-z_][A-Za-z0-9_]*\s*:/u,
  'indexed-draw': /@vertex\b/u,
  'fragment-builtins': /@builtin\s*\(\s*position\s*\)/u,
  'vertex-builtins': /@builtin\s*\(\s*vertex_index\s*\)/u,
});

function referencedResourceIds(packageValue) {
  const ids = new Set(packageValue.outputs || []);
  for (const pass of packageValue.passes || []) {
    for (const binding of pass.bindings || []) ids.add(binding.resourceId);
    for (const vertexBuffer of pass.vertexBuffers || []) ids.add(vertexBuffer.resourceId);
    if (pass.indexBuffer?.resourceId) ids.add(pass.indexBuffer.resourceId);
    for (const target of pass.targets || []) ids.add(target.resourceId);
  }
  return ids;
}

export function evaluateWgslWriterV3Quality(task, family) {
  const violations = [];
  const modules = task?.packageValue?.modules || [];
  const source = modules.map((module) => module.wgsl).join('\n');
  const resourceKinds = new Set(
    (task?.packageValue?.resources || []).map((resource) => resource.kind)
  );
  const referenced = referencedResourceIds(task?.packageValue || {});
  for (const kind of family.requiredResourceKinds || []) {
    const dualUseSampledTarget = kind === 'sampled_texture'
      && (task?.packageValue?.resources || []).some((resource) => (
        ['render_target', 'storage_texture'].includes(resource.kind)
        && resource.access === 'read_write'
      ));
    if (!resourceKinds.has(kind) && !dualUseSampledTarget) {
      violations.push(`required_resource_kind_missing:${kind}`);
    }
  }
  for (const resource of task?.packageValue?.resources || []) {
    if (!referenced.has(resource.id)) violations.push(`resource_unused:${resource.id}`);
  }
  for (const feature of family.requiredWgslFeatures || []) {
    const pattern = FEATURE_PATTERNS[feature];
    if (pattern && !pattern.test(source)) violations.push(`required_wgsl_feature_missing:${feature}`);
  }
  const passKinds = new Set((task?.packageValue?.passes || []).map((pass) => pass.kind));
  if (family.pipelineKind === 'compute' && !passKinds.has('compute')) {
    violations.push('compute_pass_missing');
  }
  if (family.pipelineKind === 'render' && !passKinds.has('render')) {
    violations.push('render_pass_missing');
  }
  if (family.pipelineKind === 'multi_pass'
    && (!passKinds.has('compute') && (task?.packageValue?.passes || []).length < 2)) {
    violations.push('multi_pass_execution_missing');
  }
  if (source.includes('```')) violations.push('markdown_fence');
  if (/\bTODO\b|\bFIXME\b/u.test(source)) violations.push('unfinished_marker');
  if (passKinds.has('compute')
    && /var\s*<\s*storage/u.test(source)
    && !/\bif\s*\(/u.test(source)) {
    violations.push('storage_compute_bounds_guard_missing');
  }
  for (const module of modules) {
    if (!/@(?:compute|vertex|fragment)\b/u.test(module.wgsl)) {
      violations.push(`module_stage_missing:${module.id}`);
    }
  }
  return {
    pass: violations.length === 0,
    violations,
    checks: {
      styleGuide: 'docs/style/wgsl-style-guide.md',
      resourceCoverage: true,
      declaredFeatureCoverage: true,
      stageCoverage: true,
      boundsGuardHeuristic: true,
      unfinishedMarkerRejection: true,
    },
  };
}

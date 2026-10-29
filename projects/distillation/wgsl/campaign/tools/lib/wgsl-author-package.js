const IDENTIFIER_PATTERN = /^[A-Za-z_][A-Za-z0-9_]*$/;
const ID_PATTERN = /^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$/;
const RESOURCE_KINDS = new Set([
  'storage_buffer',
  'uniform_buffer',
  'sampled_texture',
  'storage_texture',
  'sampler',
  'render_target',
  'vertex_buffer',
  'index_buffer',
  'render_target',
]);
const BINDABLE_RESOURCE_KINDS = new Set([
  'storage_buffer',
  'uniform_buffer',
  'sampled_texture',
  'storage_texture',
  'sampler',
  'render_target',
]);
const OUTPUT_RESOURCE_KINDS = new Set([
  'storage_buffer',
  'storage_texture',
  'render_target',
]);
const EXPRESSION_OPERATORS = new Set(['add', 'multiply', 'max', 'min', 'ceil_div']);

function isPlainObject(value) {
  return value != null && typeof value === 'object' && !Array.isArray(value);
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function pushUnique(violations, value) {
  if (!violations.includes(value)) violations.push(value);
}

function validId(value) {
  return typeof value === 'string' && ID_PATTERN.test(value);
}

function validIdentifier(value) {
  return typeof value === 'string' && IDENTIFIER_PATTERN.test(value);
}

function validateExpression(expression, options = {}, trace = 'expression', depth = 0) {
  const violations = [];
  if (depth > Number(options.maxExpressionDepth ?? 8)) {
    return [`${trace}:depth_exceeded`];
  }
  if (!isPlainObject(expression)) return [`${trace}:object_required`];
  const kind = expression.kind;
  if (kind === 'literal') {
    if (!Number.isSafeInteger(expression.value) || expression.value < 0) {
      violations.push(`${trace}:nonnegative_integer_literal_required`);
    }
    return violations;
  }
  if (kind === 'parameter' || kind === 'override') {
    if (!validIdentifier(expression.name)) violations.push(`${trace}:identifier_required`);
    const names = kind === 'parameter' ? options.parameterNames : options.overrideNames;
    if (Array.isArray(names) && !names.includes(expression.name)) {
      violations.push(`${trace}:${kind}_unknown`);
    }
    return violations;
  }
  if (kind !== 'operation') return [`${trace}:kind_unsupported`];
  if (!EXPRESSION_OPERATORS.has(expression.operator)) {
    violations.push(`${trace}:operator_unsupported`);
  }
  if (!Array.isArray(expression.operands) || expression.operands.length !== 2) {
    violations.push(`${trace}:two_operands_required`);
    return violations;
  }
  for (let index = 0; index < expression.operands.length; index += 1) {
    violations.push(...validateExpression(
      expression.operands[index],
      options,
      `${trace}.operands[${index}]`,
      depth + 1
    ));
  }
  return violations;
}

export function evaluateWgslAuthorExpression(expression, context = {}) {
  const violations = validateExpression(expression);
  if (violations.length > 0) {
    throw new Error(`Invalid WGSL author expression: ${violations.join(', ')}`);
  }
  if (expression.kind === 'literal') return expression.value;
  if (expression.kind === 'parameter') {
    const value = context.parameters?.[expression.name];
    if (!Number.isSafeInteger(value) || value < 0) {
      throw new Error(`Missing nonnegative integer parameter: ${expression.name}`);
    }
    return value;
  }
  if (expression.kind === 'override') {
    const value = context.overrides?.[expression.name];
    if (!Number.isSafeInteger(value) || value < 0) {
      throw new Error(`Missing nonnegative integer override: ${expression.name}`);
    }
    return value;
  }
  const [left, right] = expression.operands.map((operand) => (
    evaluateWgslAuthorExpression(operand, context)
  ));
  let result;
  if (expression.operator === 'add') result = left + right;
  if (expression.operator === 'multiply') result = left * right;
  if (expression.operator === 'max') result = Math.max(left, right);
  if (expression.operator === 'min') result = Math.min(left, right);
  if (expression.operator === 'ceil_div') {
    if (right === 0) throw new Error('WGSL author ceil_div denominator must be positive.');
    result = Math.ceil(left / right);
  }
  if (!Number.isSafeInteger(result) || result < 0) {
    throw new Error('WGSL author expression result must be a nonnegative safe integer.');
  }
  return result;
}

function parseDeclarations(source) {
  const declarations = [];
  const declarationPattern = /((?:@(group|binding)\s*\(\s*\d+\s*\)\s*)+)var(?:\s*<[^>]+>)?\s+([A-Za-z_][A-Za-z0-9_]*)\s*:/gu;
  for (const match of source.matchAll(declarationPattern)) {
    const attributes = match[1];
    const group = attributes.match(/@group\s*\(\s*(\d+)\s*\)/u);
    const binding = attributes.match(/@binding\s*\(\s*(\d+)\s*\)/u);
    if (!group || !binding) continue;
    declarations.push({
      group: Number(group[1]),
      binding: Number(binding[1]),
      shaderName: match[3],
    });
  }
  return declarations;
}

function hasStageEntryPoint(source, stage, entryPoint) {
  if (!validIdentifier(entryPoint)) return false;
  const stagePattern = new RegExp(
    `@${stage}\\b[\\s\\S]{0,320}?\\bfn\\s+${escapeRegExp(entryPoint)}\\s*\\(`,
    'u'
  );
  return stagePattern.test(source);
}

function validateBindings(pass, resources, source, trace) {
  const violations = [];
  const declarations = parseDeclarations(source);
  const slots = new Set();
  if (!Array.isArray(pass.bindings)) {
    return [`${trace}.bindings:array_required`];
  }
  for (const [index, binding] of pass.bindings.entries()) {
    const itemTrace = `${trace}.bindings[${index}]`;
    if (!isPlainObject(binding)) {
      violations.push(`${itemTrace}:object_required`);
      continue;
    }
    if (!Number.isInteger(binding.group) || binding.group < 0) {
      violations.push(`${itemTrace}:group_invalid`);
    }
    if (!Number.isInteger(binding.binding) || binding.binding < 0) {
      violations.push(`${itemTrace}:binding_invalid`);
    }
    const slot = `${binding.group}:${binding.binding}`;
    if (slots.has(slot)) violations.push(`${itemTrace}:slot_duplicated`);
    slots.add(slot);
    const resource = resources.get(binding.resourceId);
    if (!resource) {
      violations.push(`${itemTrace}:resource_unknown`);
    } else if (!BINDABLE_RESOURCE_KINDS.has(resource.kind)) {
      violations.push(`${itemTrace}:resource_not_bindable`);
    }
    if (!validIdentifier(binding.shaderName)) violations.push(`${itemTrace}:shader_name_invalid`);
    const declared = declarations.some((candidate) => (
      candidate.group === binding.group
      && candidate.binding === binding.binding
      && candidate.shaderName === binding.shaderName
    ));
    if (!declared) violations.push(`${itemTrace}:wgsl_declaration_missing`);
  }
  return violations;
}

function validatePipelineConstants(pass, source, contract, trace) {
  const violations = [];
  if (!Array.isArray(pass.constants)) return [`${trace}.constants:array_required`];
  const names = new Set();
  for (const [index, constant] of pass.constants.entries()) {
    const itemTrace = `${trace}.constants[${index}]`;
    if (!validIdentifier(constant?.name)) violations.push(`${itemTrace}:name_invalid`);
    if (names.has(constant?.name)) violations.push(`${itemTrace}:name_duplicated`);
    names.add(constant?.name);
    if (!new RegExp(`\\boverride\\s+${escapeRegExp(constant?.name)}\\b`, 'u').test(source)) {
      violations.push(`${itemTrace}:wgsl_override_missing`);
    }
    violations.push(...validateExpression(
      constant?.value,
      contract,
      `${itemTrace}.value`
    ));
  }
  return violations;
}

function validateDescriptorExpression(descriptor, field, contract, trace) {
  return validateExpression(descriptor?.[field], contract, `${trace}.${field}`);
}

function validateResourceDescriptor(resource, contract, trace) {
  const violations = [];
  const descriptor = resource?.descriptor;
  if (!isPlainObject(descriptor)) return [`${trace}.descriptor:object_required`];
  if (['storage_buffer', 'uniform_buffer', 'vertex_buffer', 'index_buffer']
    .includes(resource.kind)) {
    violations.push(...validateDescriptorExpression(
      descriptor,
      'byteLength',
      contract,
      `${trace}.descriptor`
    ));
  }
  if (['sampled_texture', 'storage_texture', 'render_target'].includes(resource.kind)) {
    if (typeof descriptor.format !== 'string' || descriptor.format.length === 0) {
      violations.push(`${trace}.descriptor:format_required`);
    }
    if (!['1d', '2d', '2d-array', 'cube', 'cube-array', '3d'].includes(descriptor.dimension)) {
      violations.push(`${trace}.descriptor:dimension_unsupported`);
    }
    for (const field of ['width', 'height', 'depthOrArrayLayers']) {
      violations.push(...validateDescriptorExpression(
        descriptor,
        field,
        contract,
        `${trace}.descriptor`
      ));
    }
    violations.push(...validateDescriptorExpression(
      descriptor,
      'mipLevelCount',
      contract,
      `${trace}.descriptor`
    ));
    if (!Number.isSafeInteger(descriptor.sampleCount) || descriptor.sampleCount < 1) {
      violations.push(`${trace}.descriptor:sample_count_invalid`);
    }
  }
  if (resource.kind === 'sampled_texture'
    && !['float', 'unfilterable-float', 'depth', 'sint', 'uint'].includes(descriptor.sampleType)) {
    violations.push(`${trace}.descriptor:sample_type_unsupported`);
  }
  if (resource.kind === 'sampler') {
    if (!['filtering', 'non-filtering', 'comparison'].includes(descriptor.samplerType)) {
      violations.push(`${trace}.descriptor:sampler_type_unsupported`);
    }
    for (const field of ['addressModeU', 'addressModeV', 'addressModeW']) {
      if (!['clamp-to-edge', 'repeat', 'mirror-repeat'].includes(descriptor[field])) {
        violations.push(`${trace}.descriptor:${field}_unsupported`);
      }
    }
    for (const field of ['magFilter', 'minFilter', 'mipmapFilter']) {
      if (!['nearest', 'linear'].includes(descriptor[field])) {
        violations.push(`${trace}.descriptor:${field}_unsupported`);
      }
    }
    if (!Number.isFinite(descriptor.lodMinClamp)
      || !Number.isFinite(descriptor.lodMaxClamp)
      || descriptor.lodMinClamp < 0
      || descriptor.lodMaxClamp < descriptor.lodMinClamp) {
      violations.push(`${trace}.descriptor:lod_clamp_invalid`);
    }
    const compareModes = [
      'never',
      'less',
      'equal',
      'less-equal',
      'greater',
      'not-equal',
      'greater-equal',
      'always',
    ];
    if (descriptor.samplerType === 'comparison') {
      if (!compareModes.includes(descriptor.compare)) {
        violations.push(`${trace}.descriptor:compare_required`);
      }
    } else if (descriptor.compare !== null) {
      violations.push(`${trace}.descriptor:compare_null_required`);
    }
    if (!Number.isSafeInteger(descriptor.maxAnisotropy)
      || descriptor.maxAnisotropy < 1
      || descriptor.maxAnisotropy > 16) {
      violations.push(`${trace}.descriptor:max_anisotropy_invalid`);
    }
  }
  if (resource.kind === 'vertex_buffer') {
    if (!Number.isSafeInteger(descriptor.arrayStride) || descriptor.arrayStride < 1) {
      violations.push(`${trace}.descriptor:array_stride_invalid`);
    }
    if (!['vertex', 'instance'].includes(descriptor.stepMode)) {
      violations.push(`${trace}.descriptor:step_mode_unsupported`);
    }
    if (!Array.isArray(descriptor.attributes) || descriptor.attributes.length === 0) {
      violations.push(`${trace}.descriptor:vertex_attribute_required`);
    } else {
      const locations = new Set();
      for (const [index, attribute] of descriptor.attributes.entries()) {
        const attributeTrace = `${trace}.descriptor.attributes[${index}]`;
        if (!Number.isSafeInteger(attribute?.shaderLocation) || attribute.shaderLocation < 0) {
          violations.push(`${attributeTrace}:shader_location_invalid`);
        }
        if (locations.has(attribute?.shaderLocation)) {
          violations.push(`${attributeTrace}:shader_location_duplicated`);
        }
        locations.add(attribute?.shaderLocation);
        if (!Number.isSafeInteger(attribute?.offset) || attribute.offset < 0) {
          violations.push(`${attributeTrace}:offset_invalid`);
        }
        if (typeof attribute?.format !== 'string' || attribute.format.length === 0) {
          violations.push(`${attributeTrace}:format_required`);
        }
      }
    }
  }
  if (resource.kind === 'index_buffer'
    && !['uint16', 'uint32'].includes(descriptor.indexFormat)) {
    violations.push(`${trace}.descriptor:index_format_unsupported`);
  }
  const readOnlyKinds = new Set([
    'uniform_buffer',
    'sampled_texture',
    'sampler',
    'vertex_buffer',
    'index_buffer',
  ]);
  if (readOnlyKinds.has(resource.kind) && resource.access !== 'read') {
    violations.push(`${trace}:read_access_required`);
  }
  if (resource.kind === 'render_target'
    && !['write', 'read_write'].includes(resource.access)) {
    violations.push(`${trace}:write_access_required`);
  }
  return violations;
}

function validateVertexBuffers(pass, resources, trace) {
  const violations = [];
  if (!Array.isArray(pass.vertexBuffers)) {
    return [`${trace}.vertexBuffers:array_required`];
  }
  const slots = new Set();
  for (const [index, vertexBuffer] of pass.vertexBuffers.entries()) {
    const itemTrace = `${trace}.vertexBuffers[${index}]`;
    if (!Number.isSafeInteger(vertexBuffer?.slot) || vertexBuffer.slot < 0) {
      violations.push(`${itemTrace}:slot_invalid`);
    }
    if (slots.has(vertexBuffer?.slot)) violations.push(`${itemTrace}:slot_duplicated`);
    slots.add(vertexBuffer?.slot);
    if (resources.get(vertexBuffer?.resourceId)?.kind !== 'vertex_buffer') {
      violations.push(`${itemTrace}:vertex_buffer_resource_required`);
    }
  }
  return violations;
}

function validateComputePass(pass, source, resources, contract, trace) {
  const violations = [];
  const entryPoint = pass.entryPoints?.compute;
  if (!hasStageEntryPoint(source, 'compute', entryPoint)) {
    violations.push(`${trace}:compute_entry_point_missing`);
  }
  violations.push(...validatePipelineConstants(pass, source, contract, trace));
  for (const dimension of ['x', 'y', 'z']) {
    violations.push(...validateExpression(
      pass.dispatch?.[dimension],
      contract,
      `${trace}.dispatch.${dimension}`
    ));
  }
  violations.push(...validateBindings(pass, resources, source, trace));
  return violations;
}

function validateRenderPass(pass, source, resources, contract, trace) {
  const violations = [];
  if (!hasStageEntryPoint(source, 'vertex', pass.entryPoints?.vertex)) {
    violations.push(`${trace}:vertex_entry_point_missing`);
  }
  if (!hasStageEntryPoint(source, 'fragment', pass.entryPoints?.fragment)) {
    violations.push(`${trace}:fragment_entry_point_missing`);
  }
  violations.push(...validatePipelineConstants(pass, source, contract, trace));
  const draw = pass.draw || {};
  const directFields = ['vertexCount', 'instanceCount', 'firstVertex', 'firstInstance'];
  const indexedFields = ['indexCount', 'instanceCount', 'firstIndex', 'baseVertex', 'firstInstance'];
  const fields = draw.kind === 'direct'
    ? directFields
    : draw.kind === 'indexed'
      ? indexedFields
      : [];
  if (fields.length === 0) violations.push(`${trace}.draw:kind_unsupported`);
  for (const field of fields) {
    violations.push(...validateExpression(draw[field], contract, `${trace}.draw.${field}`));
  }
  if (!['triangle-list', 'triangle-strip', 'line-list', 'line-strip', 'point-list']
    .includes(pass.primitive?.topology)) {
    violations.push(`${trace}:primitive_topology_unsupported`);
  }
  if (!['ccw', 'cw'].includes(pass.primitive?.frontFace)) {
    violations.push(`${trace}:primitive_front_face_unsupported`);
  }
  if (!['none', 'front', 'back'].includes(pass.primitive?.cullMode)) {
    violations.push(`${trace}:primitive_cull_mode_unsupported`);
  }
  if (typeof pass.primitive?.unclippedDepth !== 'boolean') {
    violations.push(`${trace}:primitive_unclipped_depth_required`);
  }
  const stripTopology = ['triangle-strip', 'line-strip'].includes(pass.primitive?.topology);
  if (stripTopology) {
    if (!['uint16', 'uint32'].includes(pass.primitive?.stripIndexFormat)) {
      violations.push(`${trace}:primitive_strip_index_format_required`);
    }
  } else if (pass.primitive?.stripIndexFormat !== null) {
    violations.push(`${trace}:primitive_strip_index_format_null_required`);
  }
  if (!isPlainObject(pass.multisample)
    || ![1, 4].includes(pass.multisample.count)
    || !Number.isSafeInteger(pass.multisample.mask)
    || pass.multisample.mask < 0
    || typeof pass.multisample.alphaToCoverageEnabled !== 'boolean') {
    violations.push(`${trace}:multisample_invalid`);
  }
  for (const field of ['x', 'y', 'width', 'height']) {
    violations.push(...validateExpression(
      pass.viewport?.[field],
      contract,
      `${trace}.viewport.${field}`
    ));
  }
  if (!Number.isFinite(pass.viewport?.minDepth)
    || !Number.isFinite(pass.viewport?.maxDepth)
    || pass.viewport.minDepth < 0
    || pass.viewport.maxDepth > 1
    || pass.viewport.minDepth > pass.viewport.maxDepth) {
    violations.push(`${trace}:viewport_depth_invalid`);
  }
  for (const field of ['x', 'y', 'width', 'height']) {
    violations.push(...validateExpression(
      pass.scissor?.[field],
      contract,
      `${trace}.scissor.${field}`
    ));
  }
  if (!Array.isArray(pass.targets) || pass.targets.length === 0) {
    violations.push(`${trace}:render_target_required`);
  } else {
    for (const [index, target] of pass.targets.entries()) {
      const resource = resources.get(target?.resourceId);
      if (!resource || resource.kind !== 'render_target') {
        violations.push(`${trace}.targets[${index}]:render_target_resource_required`);
      }
      if (typeof target?.format !== 'string' || target.format.length === 0) {
        violations.push(`${trace}.targets[${index}]:format_required`);
      } else if (resource?.descriptor?.format !== target.format) {
        violations.push(`${trace}.targets[${index}]:format_mismatch`);
      }
      if (!['clear', 'load'].includes(target?.loadOp)) {
        violations.push(`${trace}.targets[${index}]:load_op_unsupported`);
      }
      if (!['store', 'discard'].includes(target?.storeOp)) {
        violations.push(`${trace}.targets[${index}]:store_op_unsupported`);
      }
      if (target?.loadOp === 'clear') {
        if (!Array.isArray(target.clearValue)
          || target.clearValue.length !== 4
          || target.clearValue.some((channel) => !Number.isFinite(channel))) {
          violations.push(`${trace}.targets[${index}]:clear_value_invalid`);
        }
      } else if (target?.clearValue !== null) {
        violations.push(`${trace}.targets[${index}]:clear_value_null_required`);
      }
      if (target?.blend !== null) {
        violations.push(`${trace}.targets[${index}]:blend_not_supported_in_v1`);
      }
      if (!Number.isSafeInteger(target?.writeMask)
        || target.writeMask < 0
        || target.writeMask > 15) {
        violations.push(`${trace}.targets[${index}]:write_mask_invalid`);
      }
    }
  }
  violations.push(...validateVertexBuffers(pass, resources, trace));
  if (draw.kind === 'indexed') {
    if (resources.get(pass.indexBuffer?.resourceId)?.kind !== 'index_buffer') {
      violations.push(`${trace}.indexBuffer:index_buffer_resource_required`);
    }
  } else if (pass.indexBuffer !== null) {
    violations.push(`${trace}.indexBuffer:null_required_for_direct_draw`);
  }
  violations.push(...validateBindings(pass, resources, source, trace));
  return violations;
}

export function validateWgslAuthorPackage(value, contract = {}) {
  const violations = [];
  if (!isPlainObject(value)) return { ok: false, violations: ['package_object_required'] };
  if (value.schema !== 'doppler.wgsl-author-package/v1') {
    violations.push('package_schema_unsupported');
  }
  if (!isPlainObject(value.requirements)) {
    violations.push('requirements_object_required');
  } else {
    const availableFeatures = Array.isArray(contract.availableFeatures)
      ? new Set(contract.availableFeatures)
      : null;
    if (!Array.isArray(value.requirements.features)) {
      violations.push('requirements.features:array_required');
    } else {
      const features = new Set();
      for (const [index, feature] of value.requirements.features.entries()) {
        if (typeof feature !== 'string' || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/u.test(feature)) {
          violations.push(`requirements.features[${index}]:feature_invalid`);
        }
        if (features.has(feature)) {
          violations.push(`requirements.features[${index}]:feature_duplicated`);
        }
        features.add(feature);
        if (availableFeatures && !availableFeatures.has(feature)) {
          violations.push(`requirements.features[${index}]:feature_unavailable`);
        }
      }
    }
    if (!Array.isArray(value.requirements.limits)) {
      violations.push('requirements.limits:array_required');
    } else {
      const limits = new Set();
      for (const [index, limit] of value.requirements.limits.entries()) {
        const trace = `requirements.limits[${index}]`;
        if (!validIdentifier(limit?.name)) violations.push(`${trace}:name_invalid`);
        if (!Number.isSafeInteger(limit?.minimum) || limit.minimum < 0) {
          violations.push(`${trace}:minimum_invalid`);
        }
        if (limits.has(limit?.name)) violations.push(`${trace}:limit_duplicated`);
        limits.add(limit?.name);
        if (isPlainObject(contract.limits)
          && Number(contract.limits[limit?.name]) < Number(limit?.minimum)) {
          violations.push(`${trace}:limit_unavailable`);
        }
      }
    }
  }
  const modules = new Map();
  const moduleList = Array.isArray(value.modules) ? value.modules : [];
  if (moduleList.length === 0) {
    violations.push('module_required');
  } else if (moduleList.length > Number(contract.maxModules ?? 4)) {
    violations.push('module_limit_exceeded');
  }
  for (const [index, module] of moduleList.entries()) {
    const trace = `modules[${index}]`;
    if (!isPlainObject(module)) {
      violations.push(`${trace}:object_required`);
      continue;
    }
    if (!validId(module?.id)) violations.push(`${trace}:id_invalid`);
    if (modules.has(module?.id)) violations.push(`${trace}:id_duplicated`);
    const source = typeof module?.wgsl === 'string' ? module.wgsl.trim() : '';
    if (!source) violations.push(`${trace}:wgsl_required`);
    if (source.includes('```')) violations.push(`${trace}:markdown_fence`);
    if (source.length > Number(contract.maxModuleCharacters ?? 24000)) {
      violations.push(`${trace}:character_limit_exceeded`);
    }
    modules.set(module?.id, source);
  }
  const resources = new Map();
  const resourceList = Array.isArray(value.resources) ? value.resources : [];
  if (!Array.isArray(value.resources)) violations.push('resources_array_required');
  const contractResources = new Map(
    (Array.isArray(contract.resources) ? contract.resources : []).map((resource) => [
      resource.id,
      resource,
    ])
  );
  for (const [index, resource] of resourceList.entries()) {
    const trace = `resources[${index}]`;
    if (!isPlainObject(resource)) {
      violations.push(`${trace}:object_required`);
      continue;
    }
    if (!validId(resource?.id)) violations.push(`${trace}:id_invalid`);
    if (resources.has(resource?.id)) violations.push(`${trace}:id_duplicated`);
    if (!RESOURCE_KINDS.has(resource?.kind)) violations.push(`${trace}:kind_unsupported`);
    if (!['read', 'write', 'read_write'].includes(resource?.access)) {
      violations.push(`${trace}:access_unsupported`);
    }
    if (!['host', 'generated'].includes(resource?.ownership)) {
      violations.push(`${trace}:ownership_unsupported`);
    }
    if (resource?.ownership === 'generated' && contract.allowGeneratedResources === false) {
      violations.push(`${trace}:generated_resource_forbidden`);
    }
    const expected = contractResources.get(resource?.id);
    if (resource?.ownership === 'host') {
      if (!expected) {
        violations.push(`${trace}:host_resource_unknown`);
      } else {
        if (expected.kind !== resource.kind) violations.push(`${trace}:host_kind_mismatch`);
        if (expected.access !== resource.access) violations.push(`${trace}:host_access_mismatch`);
      }
    }
    violations.push(...validateResourceDescriptor(resource, contract, trace));
    resources.set(resource?.id, resource);
  }
  for (const resourceId of contractResources.keys()) {
    if (!resources.has(resourceId)) violations.push(`contract_resource_missing:${resourceId}`);
  }
  const passIds = new Set();
  const stageKinds = new Set();
  const passList = Array.isArray(value.passes) ? value.passes : [];
  if (passList.length === 0) {
    violations.push('pass_required');
  } else if (passList.length > Number(contract.maxPasses ?? 8)) {
    violations.push('pass_limit_exceeded');
  }
  for (const [index, pass] of passList.entries()) {
    const trace = `passes[${index}]`;
    if (!isPlainObject(pass)) {
      violations.push(`${trace}:object_required`);
      continue;
    }
    if (!validId(pass?.id)) violations.push(`${trace}:id_invalid`);
    if (passIds.has(pass?.id)) violations.push(`${trace}:id_duplicated`);
    passIds.add(pass?.id);
    const source = modules.get(pass?.moduleId);
    if (typeof source !== 'string') {
      violations.push(`${trace}:module_unknown`);
      continue;
    }
    if (pass.kind === 'compute') {
      stageKinds.add('compute');
      violations.push(...validateComputePass(pass, source, resources, contract, trace));
    } else if (pass.kind === 'render') {
      stageKinds.add('render');
      violations.push(...validateRenderPass(pass, source, resources, contract, trace));
    } else {
      violations.push(`${trace}:kind_unsupported`);
    }
  }
  if (!Array.isArray(value.outputs) || value.outputs.length === 0) {
    violations.push('output_required');
  } else {
    for (const [index, resourceId] of value.outputs.entries()) {
      const resource = resources.get(resourceId);
      if (!resource) {
        violations.push(`outputs[${index}]:resource_unknown`);
      } else if (!OUTPUT_RESOURCE_KINDS.has(resource.kind)
        || !['write', 'read_write'].includes(resource.access)) {
        violations.push(`outputs[${index}]:observable_output_required`);
      }
    }
  }
  const requiredStages = Array.isArray(contract.requiredStageKinds)
    ? contract.requiredStageKinds
    : [];
  for (const stage of requiredStages) {
    if (!stageKinds.has(stage)) violations.push(`required_stage_missing:${stage}`);
  }
  return { ok: violations.length === 0, violations };
}

export function parseWgslAuthorPackageResponse(response, contract = {}) {
  const violations = [];
  if (typeof response !== 'string') violations.push('non_string_response');
  const source = typeof response === 'string' ? response.trim() : '';
  if (!source) violations.push('empty_response');
  if (source.length > Number(contract.maxResponseCharacters ?? 100000)) {
    violations.push('response_character_limit_exceeded');
  }
  if (contract.forbidMarkdownFences !== false && source.includes('```')) {
    violations.push('markdown_fence');
  }
  let value = null;
  if (source) {
    try {
      value = JSON.parse(source);
    } catch {
      violations.push('malformed_json');
    }
  }
  if (value != null) {
    for (const violation of validateWgslAuthorPackage(value, contract).violations) {
      pushUnique(violations, violation);
    }
  }
  return { ok: violations.length === 0, value, source, violations };
}

export function buildWgslAuthorPrompt(task, promptContract = {}) {
  if (!isPlainObject(task)
    || typeof task.objective !== 'string'
    || !Array.isArray(task.resources)
    || !Array.isArray(task.parameters)
    || !isPlainObject(task.acceptance)) {
    throw new Error('WGSL author prompt requires objective, resources, parameters, and acceptance.');
  }
  if (promptContract.responseContract !== 'wgsl_author_package_v1') {
    throw new Error('WGSL author prompt: unsupported response contract.');
  }
  return [
    'Author an executable WebGPU shader package from the supplied objective and host contract.',
    'Return one JSON object only. Do not return Markdown or explanatory prose.',
    'The object schema is doppler.wgsl-author-package/v1.',
    'It must contain requirements{features[],limits[]}, modules[], resources[], passes[], and outputs[].',
    'Each module contains complete WGSL. Passes must bind declared resources and provide symbolic dispatch or draw expressions.',
    'Use literal, parameter, override, or binary operation expressions; allowed operations are add, multiply, max, min, and ceil_div.',
    `<task_id>${task.taskId}</task_id>`,
    '<objective>',
    task.objective.trim(),
    '</objective>',
    '<host_contract>',
    JSON.stringify({
      resources: task.resources,
      parameters: task.parameters,
      acceptance: task.acceptance,
      limits: task.limits || {},
    }, null, 2),
    '</host_contract>',
  ].join('\n');
}

export { validateExpression };

import {
  evaluateWgslAuthorExpression,
  validateWgslAuthorPackage,
} from './wgsl-author-package.js';

function isPlainObject(value) {
  return value != null && typeof value === 'object' && !Array.isArray(value);
}

function requirePositiveInteger(value, label) {
  if (!Number.isSafeInteger(value) || value < 1) {
    throw new Error(`${label} must resolve to a positive safe integer.`);
  }
  return value;
}

function requireAlignedBufferSize(value, label) {
  requirePositiveInteger(value, label);
  if (value % 4 !== 0) throw new Error(`${label} must be aligned to four bytes.`);
  return value;
}

function normalizeBytes(value, expectedLength, label) {
  if (!Array.isArray(value) && !ArrayBuffer.isView(value)) {
    throw new Error(`${label} bytes are required.`);
  }
  const bytes = Array.from(value, Number);
  if (bytes.length !== expectedLength) {
    throw new Error(`${label} byte length mismatch: expected ${expectedLength}, got ${bytes.length}.`);
  }
  for (const byte of bytes) {
    if (!Number.isSafeInteger(byte) || byte < 0 || byte > 255) {
      throw new Error(`${label} contains a value outside the byte range.`);
    }
  }
  return bytes;
}

function resolveExpression(expression, context, label) {
  const value = evaluateWgslAuthorExpression(expression, context);
  if (!Number.isSafeInteger(value) || value < 0) {
    throw new Error(`${label} must resolve to a nonnegative safe integer.`);
  }
  return value;
}

function resolveTextureDescriptor(resource, formatCatalog, context) {
  const descriptor = resource.descriptor;
  const format = formatCatalog[descriptor.format];
  if (!isPlainObject(format)) {
    throw new Error(`Unsupported WGSL author texture format: ${descriptor.format}.`);
  }
  const size = {
    width: requirePositiveInteger(
      resolveExpression(descriptor.width, context, `${resource.id}.width`),
      `${resource.id}.width`
    ),
    height: requirePositiveInteger(
      resolveExpression(descriptor.height, context, `${resource.id}.height`),
      `${resource.id}.height`
    ),
    depthOrArrayLayers: requirePositiveInteger(
      resolveExpression(
        descriptor.depthOrArrayLayers,
        context,
        `${resource.id}.depthOrArrayLayers`
      ),
      `${resource.id}.depthOrArrayLayers`
    ),
  };
  const mipLevelCount = requirePositiveInteger(
    resolveExpression(descriptor.mipLevelCount, context, `${resource.id}.mipLevelCount`),
    `${resource.id}.mipLevelCount`
  );
  if (mipLevelCount !== 1) {
    throw new Error(`${resource.id} mipmapped initialization is not supported by execution plan v1.`);
  }
  if (descriptor.sampleCount !== 1) {
    throw new Error(`${resource.id} multisampling is not supported by execution plan v1.`);
  }
  const blocksPerRow = Math.ceil(size.width / Number(format.blockWidth));
  const blockRows = Math.ceil(size.height / Number(format.blockHeight));
  const tightBytesPerRow = blocksPerRow * Number(format.bytesPerBlock);
  const tightByteLength = tightBytesPerRow * blockRows * size.depthOrArrayLayers;
  if (!Number.isSafeInteger(tightByteLength) || tightByteLength < 1) {
    throw new Error(`${resource.id} texture byte length is invalid.`);
  }
  return {
    format: descriptor.format,
    dimension: descriptor.dimension,
    size,
    mipLevelCount,
    sampleCount: descriptor.sampleCount,
    sampleType: descriptor.sampleType || null,
    copy: {
      blockWidth: format.blockWidth,
      blockHeight: format.blockHeight,
      bytesPerBlock: format.bytesPerBlock,
      tightBytesPerRow,
      blockRows,
      tightByteLength,
    },
  };
}

function bufferUsage(resource, outputIds) {
  const usage = new Set(['copy_dst']);
  if (resource.kind === 'storage_buffer') usage.add('storage');
  if (resource.kind === 'uniform_buffer') usage.add('uniform');
  if (resource.kind === 'vertex_buffer') usage.add('vertex');
  if (resource.kind === 'index_buffer') usage.add('index');
  if (outputIds.has(resource.id)) usage.add('copy_src');
  return [...usage].sort();
}

function textureUsage(resource, outputIds) {
  const usage = new Set(['copy_dst']);
  if (resource.kind === 'sampled_texture') usage.add('texture_binding');
  if (resource.kind === 'storage_texture') {
    usage.add('storage_binding');
    usage.add('texture_binding');
  }
  if (resource.kind === 'render_target') {
    usage.add('render_attachment');
    usage.add('texture_binding');
  }
  if (outputIds.has(resource.id)) usage.add('copy_src');
  return [...usage].sort();
}

function resolveInitialization(resource, resolvedDescriptor, contextResource) {
  if (resource.ownership === 'generated') return { kind: 'zero', bytes: null };
  if (!isPlainObject(contextResource)) {
    throw new Error(`Host resource payload is missing: ${resource.id}.`);
  }
  if (!['zero', 'bytes'].includes(contextResource.initialization)) {
    throw new Error(`Host resource ${resource.id} requires explicit zero or bytes initialization.`);
  }
  if (contextResource.initialization === 'zero') return { kind: 'zero', bytes: null };
  const expectedLength = resolvedDescriptor.byteLength
    ?? resolvedDescriptor.copy?.tightByteLength;
  return {
    kind: 'bytes',
    bytes: normalizeBytes(contextResource.bytes, expectedLength, resource.id),
  };
}

function resolveResource(resource, outputIds, formatCatalog, context) {
  if (['storage_buffer', 'uniform_buffer', 'vertex_buffer', 'index_buffer']
    .includes(resource.kind)) {
    const descriptor = {
      byteLength: requireAlignedBufferSize(
        resolveExpression(resource.descriptor.byteLength, context, `${resource.id}.byteLength`),
        `${resource.id}.byteLength`
      ),
      arrayStride: resource.descriptor.arrayStride ?? null,
      stepMode: resource.descriptor.stepMode ?? null,
      attributes: resource.descriptor.attributes ?? null,
      indexFormat: resource.descriptor.indexFormat ?? null,
    };
    return {
      id: resource.id,
      kind: resource.kind,
      access: resource.access,
      ownership: resource.ownership,
      descriptor,
      usage: bufferUsage(resource, outputIds),
      initialization: resolveInitialization(
        resource,
        descriptor,
        context.resources?.[resource.id]
      ),
    };
  }
  if (['sampled_texture', 'storage_texture', 'render_target'].includes(resource.kind)) {
    const descriptor = resolveTextureDescriptor(resource, formatCatalog, context);
    return {
      id: resource.id,
      kind: resource.kind,
      access: resource.access,
      ownership: resource.ownership,
      descriptor,
      usage: textureUsage(resource, outputIds),
      initialization: resolveInitialization(
        resource,
        descriptor,
        context.resources?.[resource.id]
      ),
    };
  }
  return {
    id: resource.id,
    kind: resource.kind,
    access: resource.access,
    ownership: resource.ownership,
    descriptor: structuredClone(resource.descriptor),
    usage: [],
    initialization: { kind: 'descriptor', bytes: null },
  };
}

function resolveComputePass(pass, modules, context) {
  return {
    id: pass.id,
    kind: pass.kind,
    moduleId: pass.moduleId,
    moduleSource: modules.get(pass.moduleId),
    entryPoints: structuredClone(pass.entryPoints),
    constants: Object.fromEntries(pass.constants.map((constant) => [
      constant.name,
      resolveExpression(constant.value, context, `${pass.id}.constants.${constant.name}`),
    ])),
    bindings: structuredClone(pass.bindings),
    dispatch: [
      resolveExpression(pass.dispatch.x, context, `${pass.id}.dispatch.x`),
      resolveExpression(pass.dispatch.y, context, `${pass.id}.dispatch.y`),
      resolveExpression(pass.dispatch.z, context, `${pass.id}.dispatch.z`),
    ],
  };
}

function resolveRenderPass(pass, modules, context) {
  const drawFields = pass.draw.kind === 'indexed'
    ? ['indexCount', 'instanceCount', 'firstIndex', 'baseVertex', 'firstInstance']
    : ['vertexCount', 'instanceCount', 'firstVertex', 'firstInstance'];
  return {
    id: pass.id,
    kind: pass.kind,
    moduleId: pass.moduleId,
    moduleSource: modules.get(pass.moduleId),
    entryPoints: structuredClone(pass.entryPoints),
    constants: Object.fromEntries(pass.constants.map((constant) => [
      constant.name,
      resolveExpression(constant.value, context, `${pass.id}.constants.${constant.name}`),
    ])),
    bindings: structuredClone(pass.bindings),
    vertexBuffers: structuredClone(pass.vertexBuffers),
    indexBuffer: structuredClone(pass.indexBuffer),
    draw: {
      kind: pass.draw.kind,
      ...Object.fromEntries(drawFields.map((field) => [
        field,
        resolveExpression(pass.draw[field], context, `${pass.id}.draw.${field}`),
      ])),
    },
    primitive: structuredClone(pass.primitive),
    multisample: structuredClone(pass.multisample),
    viewport: {
      x: resolveExpression(pass.viewport.x, context, `${pass.id}.viewport.x`),
      y: resolveExpression(pass.viewport.y, context, `${pass.id}.viewport.y`),
      width: resolveExpression(pass.viewport.width, context, `${pass.id}.viewport.width`),
      height: resolveExpression(pass.viewport.height, context, `${pass.id}.viewport.height`),
      minDepth: pass.viewport.minDepth,
      maxDepth: pass.viewport.maxDepth,
    },
    scissor: {
      x: resolveExpression(pass.scissor.x, context, `${pass.id}.scissor.x`),
      y: resolveExpression(pass.scissor.y, context, `${pass.id}.scissor.y`),
      width: resolveExpression(pass.scissor.width, context, `${pass.id}.scissor.width`),
      height: resolveExpression(pass.scissor.height, context, `${pass.id}.scissor.height`),
    },
    targets: structuredClone(pass.targets),
  };
}

export function buildWgslAuthorExecutionPlan(value, contract, context) {
  if (!isPlainObject(contract)
    || !isPlainObject(context)
    || !isPlainObject(contract.formats)
    || !isPlainObject(contract.allocationLimits)
    || !isPlainObject(context.parameters)
    || !isPlainObject(context.overrides)
    || !isPlainObject(context.resources)) {
    throw new Error(
      'WGSL author execution plan requires contract formats, allocation limits, and explicit parameter, override, and resource contexts.'
    );
  }
  const validation = validateWgslAuthorPackage(value, contract);
  if (!validation.ok) {
    throw new Error(`WGSL author package is invalid: ${validation.violations.join(', ')}`);
  }
  const expressionContext = {
    parameters: context.parameters,
    overrides: context.overrides,
  };
  const outputIds = new Set(value.outputs);
  const modules = new Map(value.modules.map((module) => [module.id, module.wgsl]));
  const resources = value.resources.map((resource) => resolveResource(
    resource,
    outputIds,
    contract.formats,
    { ...expressionContext, resources: context.resources }
  ));
  const maxBufferBytes = requirePositiveInteger(
    contract.allocationLimits.maxBufferBytes,
    'allocationLimits.maxBufferBytes'
  );
  const maxTextureBytes = requirePositiveInteger(
    contract.allocationLimits.maxTextureBytes,
    'allocationLimits.maxTextureBytes'
  );
  const maxTotalBytes = requirePositiveInteger(
    contract.allocationLimits.maxTotalBytes,
    'allocationLimits.maxTotalBytes'
  );
  let totalBytes = 0;
  for (const resource of resources) {
    const byteLength = resource.descriptor.byteLength
      ?? resource.descriptor.copy?.tightByteLength
      ?? 0;
    if (resource.kind.endsWith('_buffer') && byteLength > maxBufferBytes) {
      throw new Error(`${resource.id} exceeds allocationLimits.maxBufferBytes.`);
    }
    if (!resource.kind.endsWith('_buffer')
      && resource.kind !== 'sampler'
      && byteLength > maxTextureBytes) {
      throw new Error(`${resource.id} exceeds allocationLimits.maxTextureBytes.`);
    }
    totalBytes += byteLength;
    if (!Number.isSafeInteger(totalBytes) || totalBytes > maxTotalBytes) {
      throw new Error('WGSL author resources exceed allocationLimits.maxTotalBytes.');
    }
  }
  const passes = value.passes.map((pass) => (
    pass.kind === 'compute'
      ? resolveComputePass(pass, modules, expressionContext)
      : resolveRenderPass(pass, modules, expressionContext)
  ));
  return {
    schema: 'doppler.wgsl-author-execution-plan/v1',
    packageSchema: value.schema,
    requirements: structuredClone(value.requirements),
    parameters: structuredClone(context.parameters),
    overrides: structuredClone(context.overrides),
    modules: value.modules.map((module) => structuredClone(module)),
    resources,
    passes,
    outputs: [...value.outputs],
  };
}

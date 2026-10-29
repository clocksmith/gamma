function cloneValue(value) {
  return JSON.parse(JSON.stringify(value));
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function renameIdentifiers(source, names) {
  let output = source;
  for (const [from, to] of [...names.entries()].sort((left, right) => (
    right[0].length - left[0].length
  ))) {
    output = output.replace(new RegExp(`\\b${escapeRegExp(from)}\\b`, 'g'), to);
  }
  return output;
}

function rotate(values, offset) {
  if (values.length < 2) return [...values];
  const normalized = offset % values.length;
  return [...values.slice(normalized), ...values.slice(0, normalized)];
}

function bindingKey(group, binding) {
  return `${group}:${binding}`;
}

function collectModuleBindings(packageValue, moduleId) {
  const bindings = new Map();
  for (const pass of packageValue.passes) {
    if (pass.moduleId !== moduleId) continue;
    for (const entry of pass.bindings) {
      bindings.set(bindingKey(entry.group, entry.binding), {
        group: entry.group,
        binding: entry.binding,
      });
    }
  }
  return [...bindings.values()].sort((left, right) => (
    left.group - right.group || left.binding - right.binding
  ));
}

function bindingPermutation(entries, ordinal) {
  const byGroup = new Map();
  for (const entry of entries) {
    const group = byGroup.get(entry.group) || [];
    group.push(entry.binding);
    byGroup.set(entry.group, group);
  }
  const mapping = new Map();
  for (const [group, bindings] of byGroup) {
    const targets = rotate(bindings, ordinal);
    bindings.forEach((binding, index) => {
      mapping.set(bindingKey(group, binding), targets[index]);
    });
  }
  return mapping;
}

function permuteWgslBindings(source, entries, mapping) {
  let output = source;
  const placeholders = [];
  for (const [index, entry] of entries.entries()) {
    const pattern = new RegExp(
      `@group\\(\\s*${entry.group}\\s*\\)\\s*@binding\\(\\s*${entry.binding}\\s*\\)`,
      'g'
    );
    const matches = output.match(pattern) || [];
    if (matches.length !== 1) {
      throw new Error(
        `WGSL package diversity expected one declaration for group ${entry.group} binding ${entry.binding}, got ${matches.length}.`
      );
    }
    const placeholder = `__doppler_binding_${index}__`;
    placeholders.push({ placeholder, entry });
    output = output.replace(pattern, placeholder);
  }
  for (const { placeholder, entry } of placeholders) {
    const target = mapping.get(bindingKey(entry.group, entry.binding));
    output = output.replace(
      placeholder,
      `@group(${entry.group}) @binding(${target})`
    );
  }
  return output;
}

function moduleIdentifierMap(packageValue, moduleId, suffix) {
  const names = new Map();
  for (const pass of packageValue.passes) {
    if (pass.moduleId !== moduleId) continue;
    for (const entryPoint of Object.values(pass.entryPoints)) {
      names.set(entryPoint, `${entryPoint}_${suffix}`);
    }
    for (const binding of pass.bindings) {
      names.set(binding.shaderName, `${binding.shaderName}_${suffix}`);
    }
  }
  return names;
}

function renamePackageIdentifiers(packageValue, ordinal) {
  const suffix = `v${ordinal.toString(36)}`;
  const moduleIds = new Map(packageValue.modules.map((module) => [
    module.id,
    `${module.id}-${suffix}`,
  ]));
  for (const module of packageValue.modules) {
    const names = moduleIdentifierMap(packageValue, module.id, suffix);
    const entries = collectModuleBindings(packageValue, module.id);
    const permutation = bindingPermutation(entries, ordinal);
    module.wgsl = renameIdentifiers(
      permuteWgslBindings(module.wgsl, entries, permutation),
      names
    );
    for (const pass of packageValue.passes) {
      if (pass.moduleId !== module.id) continue;
      pass.moduleId = moduleIds.get(module.id);
      pass.entryPoints = Object.fromEntries(Object.entries(pass.entryPoints).map(([
        stage,
        entryPoint,
      ]) => [stage, names.get(entryPoint)]));
      pass.bindings = pass.bindings.map((binding) => ({
        ...binding,
        binding: permutation.get(bindingKey(binding.group, binding.binding)),
        shaderName: names.get(binding.shaderName),
      }));
    }
    module.id = moduleIds.get(module.id);
  }
  packageValue.passes = packageValue.passes.map((pass) => ({
    ...pass,
    id: `${pass.id}-${suffix}`,
    bindings: rotate(pass.bindings, ordinal),
  }));
  packageValue.modules = rotate(packageValue.modules, ordinal);
  packageValue.resources = rotate(packageValue.resources, ordinal);
  return packageValue;
}

export function diversifyWgslWriterV3Package(packageValue, ordinal, policy) {
  if (policy.mode !== 'identifier_binding_permutation_v1') {
    throw new Error(`Unsupported WGSL writer v3 package diversity mode: ${policy.mode}.`);
  }
  if (!Number.isSafeInteger(ordinal) || ordinal < 0) {
    throw new Error('WGSL writer v3 package diversity ordinal must be a non-negative integer.');
  }
  const diversified = cloneValue(packageValue);
  if (ordinal === 0) return diversified;
  return renamePackageIdentifiers(diversified, ordinal);
}

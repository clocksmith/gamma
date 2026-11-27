function lookup(root, path) {
  const segments = path.split(".").filter(Boolean);
  let value = root;
  for (const segment of segments) {
    if (
      value === null ||
      typeof value !== "object" ||
      !Object.prototype.hasOwnProperty.call(value, segment)
    ) {
      throw new Error(`Unknown content reference: \${${path}}`);
    }
    value = value[segment];
  }
  return value;
}

function parseReference(reference) {
  const [path, ...formatters] = reference.split("|").map((segment) => segment.trim());
  if (!path || formatters.some((formatter) => !formatter)) {
    throw new Error(`Invalid content reference: \${${reference}}`);
  }
  return { path, formatters };
}

function formatValue(value, formatter, variables) {
  if (formatter === "trim") {
    if (typeof value !== "string") throw new Error("Trim formatter requires a string.");
    return value.trim();
  }
  if (formatter === "headings-up") {
    if (typeof value !== "string") throw new Error("Heading formatter requires a string.");
    return value.replace(/^#{2,6} /gm, heading => heading.slice(1));
  }
  if (formatter.startsWith("label:")) {
    const labels = lookup(variables, formatter.slice("label:".length));
    if (typeof value !== "string" || !labels || !Object.hasOwn(labels, value)) {
      throw new Error(`Unknown content label: ${value}`);
    }
    return labels[value];
  }
  if (formatter !== "capitalize") {
    throw new Error(`Unknown content formatter: ${formatter}`);
  }
  if (typeof value !== "string") {
    throw new Error(`Content formatter ${formatter} requires a string value`);
  }
  const [firstCharacter = "", ...remainingCharacters] = Array.from(value);
  return `${firstCharacter.toUpperCase()}${remainingCharacters.join("")}`;
}

function resolveReference(reference, variables, stack, onReference) {
  const { path, formatters } = parseReference(reference);
  onReference?.(path);
  for (const formatter of formatters) if (formatter.startsWith("label:")) onReference?.(formatter.slice(6));
  if (stack.includes(path)) {
    throw new Error(`Circular content reference: ${[...stack, path].join(" -> ")}`);
  }
  const resolved = resolveValue(lookup(variables, path), variables, [...stack, path], onReference);
  return formatters.reduce((value, formatter) => formatValue(value, formatter, variables), resolved);
}

export function resolveString(value, variables, stack = [], onReference) {
  const exact = value.match(/^\$\{([^}]+)\}$/);
  if (exact) return resolveReference(exact[1], variables, stack, onReference);
  return value.replace(/\$\{([^}]+)\}/g, (_, reference) => {
    const { path } = parseReference(reference);
    if (stack.includes(path)) {
      throw new Error(`Circular content reference: ${[...stack, path].join(" -> ")}`);
    }
    const resolved = resolveReference(reference, variables, stack, onReference);
    if (resolved === null || typeof resolved === "object") {
      throw new Error(`Embedded content reference must resolve to a scalar: \${${reference}}`);
    }
    return String(resolved);
  });
}

export function resolveValue(value, variables, stack = [], onReference) {
  if (typeof value === "string") return resolveString(value, variables, stack, onReference);
  if (Array.isArray(value)) return value.map((entry) => resolveValue(entry, variables, stack, onReference));
  if (value && typeof value === "object") {
    if (Object.hasOwn(value, "loreRef")) {
      const { loreRef, ...record } = value;
      if (typeof loreRef !== "string" || !variables.lore || !Object.hasOwn(variables.lore, loreRef)) {
        throw new Error(`Unknown lore reference: ${loreRef}`);
      }
      const copy = variables.lore[loreRef];
      for (const key of Object.keys(copy)) {
        if (Object.hasOwn(record, key)) throw new Error(`Lore copy conflicts with component field: ${loreRef}/${key}`);
      }
      const reference = `lore.${loreRef}`;
      onReference?.(reference);
      if (stack.includes(reference)) throw new Error(`Circular lore reference: ${loreRef}`);
      value = { ...record, ...resolveValue(copy, variables, [...stack, reference], onReference) };
    }
    return Object.fromEntries(
      Object.entries(value).map(([key, entry]) => [
        resolveString(key, variables, stack, onReference),
        resolveValue(entry, variables, stack, onReference)
      ])
    );
  }
  return value;
}

export function assertNoReferences(value, label) {
  const serialized = typeof value === "string" ? value : JSON.stringify(value);
  const match = serialized.match(/\$\{[^}]+\}/);
  if (match) throw new Error(`Unresolved content reference in ${label}: ${match[0]}`);
}

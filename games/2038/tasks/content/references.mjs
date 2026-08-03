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

function formatValue(value, formatter) {
  if (formatter !== "capitalize") {
    throw new Error(`Unknown content formatter: ${formatter}`);
  }
  if (typeof value !== "string") {
    throw new Error(`Content formatter ${formatter} requires a string value`);
  }
  const [firstCharacter = "", ...remainingCharacters] = Array.from(value);
  return `${firstCharacter.toUpperCase()}${remainingCharacters.join("")}`;
}

function resolveReference(reference, variables, stack) {
  const { path, formatters } = parseReference(reference);
  const resolved = resolveValue(lookup(variables, path), variables, [...stack, path]);
  return formatters.reduce(formatValue, resolved);
}

export function resolveString(value, variables, stack = []) {
  const exact = value.match(/^\$\{([^}]+)\}$/);
  if (exact) return resolveReference(exact[1], variables, stack);
  return value.replace(/\$\{([^}]+)\}/g, (_, reference) => {
    const { path } = parseReference(reference);
    if (stack.includes(path)) {
      throw new Error(`Circular content reference: ${[...stack, path].join(" -> ")}`);
    }
    const resolved = resolveReference(reference, variables, stack);
    if (resolved === null || typeof resolved === "object") {
      throw new Error(`Embedded content reference must resolve to a scalar: \${${reference}}`);
    }
    return String(resolved);
  });
}

export function resolveValue(value, variables, stack = []) {
  if (typeof value === "string") return resolveString(value, variables, stack);
  if (Array.isArray(value)) return value.map((entry) => resolveValue(entry, variables, stack));
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, entry]) => [
        resolveString(key, variables, stack),
        resolveValue(entry, variables, stack)
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

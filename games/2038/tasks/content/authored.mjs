// Author-only metadata never enters a playable component or template context.
export function playerContent(value) {
  if (Array.isArray(value)) return value.map(playerContent);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(Object.entries(value)
    .filter(([key]) => !key.startsWith("$"))
    .map(([key, entry]) => [key, playerContent(entry)]));
}

export function documentSection(source, name) {
  if (!/^[a-z][a-z0-9-]*$/.test(name)) throw new Error(`Invalid document section: ${name}`);
  const start = `<!-- ${name}:start -->`;
  const end = `<!-- ${name}:end -->`;
  if (source.split(start).length !== 2 || source.split(end).length !== 2) {
    throw new Error(`Document must contain exactly one ${name} section.`);
  }
  const begin = source.indexOf(start) + start.length;
  const finish = source.indexOf(end);
  if (finish < begin) throw new Error(`Reversed document section: ${name}`);
  return source.slice(begin, finish).replace(/^\r?\n/, "");
}

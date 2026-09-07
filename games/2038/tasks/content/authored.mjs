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

// Named excerpts have one authored location and may appear in several readers.
export function documentSections(source) {
  const sections = {};
  const markers = [...source.matchAll(/<!-- ([a-z][a-z0-9-]*):(start|end) -->/g)];
  for (const [, name] of markers) {
    if (!Object.hasOwn(sections, name)) sections[name] = documentSection(source, name);
  }
  return sections;
}

export function stripSectionMarkers(source) {
  return source.replace(/^<!-- [a-z][a-z0-9-]*:(?:start|end) -->\r?\n/gm, "")
    .replace(/^<!-- ending:[a-z_]+ scenario:[a-z0-9-]+ -->\r?\n/gm, "");
}

export function omitDocumentSections(source, names = []) {
  if (!Array.isArray(names)) throw new Error("Excluded document sections must be an array.");
  for (const name of names) {
    documentSection(source, name);
    const start = source.indexOf(`<!-- ${name}:start -->`);
    const end = source.indexOf(`<!-- ${name}:end -->`) + `<!-- ${name}:end -->`.length;
    source = source.slice(0, start) + source.slice(end).replace(/^\r?\n/, "");
  }
  return source;
}

// Layouts may arrange titles, field labels, tables and sourced excerpts. They
// cannot add independent paragraphs, durations, quantities or effect prose.
export function validateReferenceLayout(source, path) {
  const lines = source.split(/\r?\n/);
  for (const [index, line] of lines.entries()) {
    if (!line.trim() || /^#{1,6} /.test(line)) continue;
    const residue = line.replace(/\$\{[^}]+\}/g, "")
      .replace(/\*\*[^*\d]+:\*\*/g, "").replace(/[\s*_:;,>—.()\-/·|]+/g, "");
    const separator = lines[index + 1] || "";
    const tableHeading = /^\|/.test(line) && !line.includes("${") && !/\d/.test(line)
      && /^\|[\s|:-]+$/.test(separator) && separator.includes("---");
    if (residue && !tableHeading) {
      throw new Error(`Reference layout contains unsourced prose: ${path}:${index + 1}`);
    }
  }
}

// Strict named Markdown tables share the same section ownership as excerpts.
export function documentTable(source, name, columns) {
  const lines = documentSection(source, name).trim().split(/\r?\n/);
  const cells = line => {
    if (!/^\|.*\|$/.test(line) || line.includes("\0")) throw new Error(`Malformed ${name} table row`);
    return line.slice(1, -1).replace(/\\\|/g, "\0").split("|")
      .map(value => value.replace(/\0/g, "|").trim());
  };
  const separator = cells(lines[1] || "");
  if (JSON.stringify(cells(lines[0])) !== JSON.stringify(columns) || separator.length !== columns.length ||
      separator.some(value => !/^:?-{3,}:?$/.test(value))) {
    throw new Error(`Unexpected ${name} table columns`);
  }
  if (lines.length < 3) throw new Error(`Empty ${name} table`);
  return lines.slice(2).map(line => {
    const values = cells(line);
    if (values.length !== columns.length || values.some(value => !value)) throw new Error(`Incomplete ${name} table row`);
    return Object.fromEntries(columns.map((column, index) => [column, values[index]]));
  });
}

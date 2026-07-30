const copyUrl = new URL("../../data/simulation-copy.json", import.meta.url);

async function readJson(url) {
  if (url.protocol === "file:") {
    const { readFile } = await import("node:fs/promises");
    return JSON.parse(await readFile(url, "utf8"));
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Could not load simulation copy: ${response.status}.`);
  }
  return response.json();
}

export const simulationCopy = await readJson(copyUrl);

export function renderSimulationCopy(template, values = {}) {
  return template.replace(/\{([^}]+)\}/g, (match, key) =>
    Object.prototype.hasOwnProperty.call(values, key) ? String(values[key]) : match
  );
}

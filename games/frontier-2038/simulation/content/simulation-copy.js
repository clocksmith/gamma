import { readFile } from "node:fs/promises";

const copyUrl = new URL("../../data/simulation-copy.json", import.meta.url);

export const simulationCopy = JSON.parse(await readFile(copyUrl, "utf8"));

export function renderSimulationCopy(template, values = {}) {
  return template.replace(/\{([^}]+)\}/g, (match, key) =>
    Object.prototype.hasOwnProperty.call(values, key) ? String(values[key]) : match
  );
}

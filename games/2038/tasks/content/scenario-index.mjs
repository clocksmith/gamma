import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { documentSection } from "./authored.mjs";

const root = resolve(import.meta.dirname, "../..");
const readJson = async path => JSON.parse(await readFile(resolve(root, path), "utf8"));

// Derive paths and surface IDs from the records themselves. Authors never
// maintain a second list of component paths or reverse scenario bindings.
export async function scenarioSurfaces() {
  const specifications = [
    ["components/headlines.json", "headlines", "headline", "round"],
    ["components/mandates.json", "mandates", "mandate", "era"],
    ["components/reference-cards.json", "eraCards", "reference", "round"],
    ["components/projects.json", "projects", "project", "unlockedRound"],
    ["components/projects.json", "institutionalHistory", "history", "unlockedRound"],
    ["components/factions.json", "factions", "faction", "round"],
    ["components/world.json", "endings", "ending", null]
  ];
  const surfaces = [];
  for (const [path, collection, kind, eraKey] of specifications) {
    const document = await readJson(path);
    for (const record of document[collection]) {
      const entries = kind === "faction" ? [...record.abilities, ...(record.lore || [])] : [record];
      for (const entry of entries) {
        const identity = kind === "faction" ? `${record.id}:${entry.id}` : entry.id;
        const pointer = kind === "faction" ? `${record.id}/${record.abilities.includes(entry) ? "abilities" : "lore"}/${entry.id}` : entry.id;
        surfaces.push({
          surfaceId: `${kind}:${identity}`,
          eraOrder: eraKey ? entry[eraKey] : 4,
          copyReference: `${path}#${collection}/${pointer}`,
          record: entry
        });
      }
    }
  }
  return surfaces;
}

export function assembleScenarioIndex({ surfaces, backlog, deploymentProfiles }) {
  const scenarios = new Map();
  const eras = [];
  const addScenario = notes => {
    if (!notes?.id || scenarios.has(notes.id)) throw new Error(`Duplicate or missing scenario definition: ${notes?.id}`);
    if ("surfaceBindings" in notes) throw new Error(`Scenario bindings must be generated: ${notes.id}`);
    const { eraRelation, ...definition } = notes;
    scenarios.set(notes.id, { ...definition, surfaceBindings: [] });
  };
  for (const scenario of backlog) addScenario(scenario);
  for (const { surfaceId, record } of surfaces) {
    if (record.$era) eras.push({ ...record.$era, referenceSurface: surfaceId });
    const notes = record.$scenario;
    if (!notes || typeof notes !== "object") throw new Error(`Missing scenario notes: ${surfaceId}`);
    if (!notes.ref) addScenario(notes);
    else if (Object.keys(notes).some(key => !["ref", "eraRelation"].includes(key))) {
      throw new Error(`Scenario reference must not redefine its scenario: ${surfaceId}`);
    }
  }
  for (const { surfaceId, copyReference, record } of surfaces) {
    const notes = record.$scenario;
    const scenario = scenarios.get(notes.ref || notes.id);
    if (!scenario) throw new Error(`Unknown scenario reference: ${notes.ref}`);
    const binding = { surfaceId, copyReference };
    if (notes.eraRelation !== undefined) binding.eraRelation = notes.eraRelation;
    scenario.surfaceBindings.push(binding);
  }
  return {
    $schema: "mandate2038.era-situation-ledger/v1",
    schemaVersion: 1,
    editorialAuthority: "world.md",
    deploymentProfiles,
    eras: eras.sort((a, b) => a.order - b.order),
    scenarios: [...scenarios.values()].sort((a, b) => a.id.localeCompare(b.id, "en"))
  };
}

export async function buildScenarioIndex() {
  const graph = await readJson("content/graph.json");
  if (graph.world !== "world.md") throw new Error("The world source must be world.md.");
  const world = await readFile(resolve(root, graph.world), "utf8");
  const section = documentSection(world, "scenario-backlog").trim();
  const match = /^```json\r?\n([\s\S]*)\r?\n```$/.exec(section);
  if (!match) throw new Error("Scenario backlog must be one JSON code block in world.md.");
  const backlog = JSON.parse(match[1]);
  if (!Array.isArray(backlog)) throw new Error("Scenario backlog must be an array.");
  return assembleScenarioIndex({
    surfaces: await scenarioSurfaces(), backlog, deploymentProfiles: graph.deploymentProfiles
  });
}

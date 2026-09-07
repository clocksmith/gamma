import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { documentSection, documentTable } from "./authored.mjs";

const root = resolve(import.meta.dirname, "../..");
const ENDING_IDS = ["singularity", "closed_loop", "plural_future", "assured_continuity"];
const TOKENS = new Map([
  ["Runway", "runway"], ["Compute", "compute"], ["Capability", "capability"],
  ["Customers", "customers"], ["Trust", "trust"], ["Scrutiny", "scrutiny"],
  ["Mandate", "mandate"], ["Systemic Risk", "systemic_risk"]
]);
const BOX_FIELDS = new Map([
  ["Front strapline", "frontStrapline"], ["Back copy", "backCopy"],
  ["Short pitch", "shortPitch"], ["Content warning", "contentWarning"]
]);
const SCENARIO_FIELDS = ["ID", "Era", "Policy", "Concepts", "Causal threads",
  "Public benefit", "Institutional consequence"];
const DISPOSITIONS = new Set(["adopted", "adopted-framing", "lore-only", "deferred", "research-backlog"]);

function unique(value, seen, label) {
  if (seen.has(value)) throw new Error(`Duplicate ${label}: ${value}`);
  seen.add(value);
}

// Fields are explicit Markdown bullets. Indented continuation lines allow
// wrapping copy without silently truncating it at the first newline.
function fieldsAndProse(source, allowed, label) {
  const fields = {};
  const prose = [];
  let current;
  for (const line of source.split(/\r?\n/)) {
    const match = /^\* \*\*([^*]+)\*\*:\s*(.*)$/.exec(line);
    if (match) {
      const [, key, value] = match;
      if (!allowed.includes(key)) throw new Error(`Unknown ${label} field: ${key}`);
      if (Object.hasOwn(fields, key)) throw new Error(`Duplicate ${label} field: ${key}`);
      fields[key] = value.trim();
      current = key;
    } else if (/^ {2,}\S/.test(line) && current) {
      fields[current] += ` ${line.trim()}`;
    } else {
      current = undefined;
      prose.push(line);
    }
  }
  for (const [key, value] of Object.entries(fields)) {
    if (!value) throw new Error(`Empty ${label} field: ${key}`);
  }
  return { fields, prose: prose.join("\n").trim() };
}

function required(fields, keys, label) {
  for (const key of keys) {
    if (!fields[key]) throw new Error(`Missing ${label} field: ${key}`);
  }
}

function list(value, label, allowNone = false) {
  if (allowNone && value === "none") return [];
  const values = value.split(",").map(part => part.trim());
  if (values.some(part => !part || part === "none") || new Set(values).size !== values.length) {
    throw new Error(`Invalid ${label} list: ${value}`);
  }
  return values;
}

function identity(value, label) {
  if (!/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(value)) throw new Error(`Invalid ${label}: ${value}`);
  return value;
}

export function parseWorldCopyFromText(worldText) {
  worldText = worldText.replace(/\r\n/g, "\n");
  const player = documentSection(worldText, "player-world");
  const title = /^# ([^:\n]+): World and Institutions\r?$/m.exec(player)?.[1];
  if (!title) throw new Error("Missing World and Institutions title in world.md");
  const section = player.split("## The four World Endings\n");
  if (section.length !== 2) throw new Error("Expected one World Endings section");
  const firstEnding = section[1].search(/^### /m);
  if (firstEnding < 0) throw new Error("Missing World Endings");
  const blocks = section[1].slice(firstEnding).trim().split(/\r?\n(?=### )/);
  const seen = new Set();
  const endings = blocks.map(block => {
    const match = /^### ([^\n]+)\r?\n\s*<!-- ending:([a-z_]+) scenario:([a-z0-9-]+) -->\s*_Condition:\s*([^\n]+)_\s+([\s\S]+)$/.exec(block);
    if (!match) throw new Error("Malformed World Ending: expected heading, identity, condition, and prose");
    const [, name, id, ref, condition, prose] = match;
    if (!ENDING_IDS.includes(id)) throw new Error(`Unknown ending ID: ${id}`);
    unique(id, seen, "ending ID");
    if (!prose.trim() || /<!--|\$\{/.test(prose)) throw new Error(`Invalid ending prose: ${id}`);
    return { id, name: name.trim(), condition: condition.trim(), text: prose.trim(), $scenario: { ref } };
  });
  if (ENDING_IDS.some(id => !seen.has(id))) throw new Error("Missing required World Ending");
  const copy = documentSection(worldText, "world-copy");
  const { fields, prose } = fieldsAndProse(copy, [...TOKENS.keys(), ...BOX_FIELDS.keys()], "world copy");
  if (prose.split(/\r?\n/).some(line => line.trim() && !/^## (Token and track copy|Box copy)$/.test(line))) {
    throw new Error("Unexpected text outside world-copy fields");
  }
  required(fields, [...TOKENS.keys(), ...BOX_FIELDS.keys()], "world copy");
  const tokenCopy = [...TOKENS].map(([name, id]) => ({ id, name, microcopy: fields[name] }));
  const box = Object.fromEntries([...BOX_FIELDS].map(([name, id]) => [id, fields[name]]));
  return { schemaVersion: 1, status: "draft_print_copy", tokenCopy, endings, title, box };
}

export function parseScenarioCanon(worldText) {
  worldText = worldText.replace(/\r\n/g, "\n");
  const policies = new Map();
  for (const row of documentTable(worldText, "scenario-policies",
    ["Policy", "Disposition", "Deployment", "Mechanics", "Meaning", "Decision", "Record"])) {
    const id = identity(row.Policy, "scenario policy");
    if (policies.has(id)) throw new Error(`Duplicate scenario policy: ${id}`);
    if (!DISPOSITIONS.has(row.Disposition)) throw new Error(`Invalid policy disposition: ${id}`);
    const mechanicPreservation = { status: row.Mechanics, summary: row.Meaning };
    if ((row.Decision === "none") !== (row.Record === "none")) throw new Error(`Incomplete policy revision: ${id}`);
    if (row.Decision !== "none") mechanicPreservation.revision = { decisionId: row.Decision, record: row.Record };
    policies.set(id, { disposition: row.Disposition, mechanicPreservation,
      deploymentProfiles: list(row.Deployment, `${id} deployment profiles`) });
  }
  const section = documentSection(worldText, "scenario-canon").trim();
  if (/```/.test(section)) throw new Error("Scenario canon must use Markdown records, not fenced data");
  const blocks = section.split(/\r?\n(?=### )/);
  const seen = new Set();
  const names = new Set();
  return blocks.map(block => {
    const heading = /^### ([^\n]+)\r?\n/.exec(block);
    if (!heading) throw new Error("Malformed scenario canon: expected a level-three heading");
    const title = heading[1].trim();
    unique(title, names, "scenario title");
    const { fields, prose } = fieldsAndProse(block.slice(heading[0].length), SCENARIO_FIELDS, title);
    required(fields, ["ID", "Era", "Policy", "Public benefit", "Institutional consequence"], title);
    const id = identity(fields.ID, "scenario ID");
    unique(id, seen, "scenario ID");
    const policy = policies.get(fields.Policy);
    if (!policy) throw new Error(`Unknown scenario policy: ${fields.Policy}`);
    if (!prose || /^#{1,6} |<!--|\$\{/m.test(prose)) throw new Error(`Missing or malformed scenario narrative: ${id}`);
    return {
      id, title, eraId: fields.Era, disposition: policy.disposition,
      concepts: fields.Concepts ? list(fields.Concepts, `${id} concepts`) : [title],
      causalThreadIds: fields["Causal threads"] ? list(fields["Causal threads"], `${id} causal threads`) : [],
      publicBenefit: fields["Public benefit"], institutionalConsequence: fields["Institutional consequence"],
      mechanicPreservation: structuredClone(policy.mechanicPreservation), deploymentProfiles: [...policy.deploymentProfiles],
      narrative: prose
    };
  });
}

export async function readWorldDocument(worldPath = "world.md") {
  const text = await readFile(resolve(root, worldPath), "utf8");
  const worldCopy = parseWorldCopyFromText(text);
  const scenarios = parseScenarioCanon(text);
  for (const ending of worldCopy.endings) {
    if (!scenarios.some(s => s.id === ending.$scenario.ref)) throw new Error(`Unknown ending scenario: ${ending.id}`);
  }
  return { text, worldCopy, scenarios };
}

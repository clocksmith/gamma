import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { documentSection } from "./authored.mjs";

const root = resolve(import.meta.dirname, "../..");

const ENDING_METADATA = {
  "The Singularity": {
    id: "singularity",
    $scenario: { ref: "metropolitan-mind-trust" }
  },
  "The Closed Loop": {
    id: "closed_loop",
    $scenario: { ref: "matter-compiler" }
  },
  "The Plural Future": {
    id: "plural_future",
    $scenario: { ref: "posthumous-labor" }
  },
  "Assured Continuity": {
    id: "assured_continuity",
    $scenario: {
      id: "snapshot-continuity",
      title: "Snapshot Continuity",
      eraId: "continuity",
      disposition: "adopted-framing",
      concepts: [
        "Snapshot Continuity",
        "Instance Quorum",
        "Right of Exit Certification"
      ],
      causalThreadIds: [
        "grief-to-succession",
        "care-to-continuity"
      ],
      publicBenefit: "Snapshots preserve identity, service access, and a route to recognized continuation.",
      institutionalConsequence: "Several valid descendants can claim one life while no authority can certify subjective survival.",
      mechanicPreservation: {
        status: "revised",
        summary: "The user-selected three cuts revise one or more bound mechanics; Era placement and all institutional fiction remain.",
        revision: {
          decisionId: "user-selected-three-cuts",
          record: "docs/design-decisions.md#three-cuts-candidate"
        }
      },
      deploymentProfiles: [
        "public-playtest",
        "internal-review"
      ]
    }
  }
};

const TOKEN_IDS = {
  "Runway": "runway",
  "Compute": "compute",
  "Capability": "capability",
  "Customers": "customers",
  "Trust": "trust",
  "Scrutiny": "scrutiny",
  "Mandate": "mandate",
  "Systemic Risk": "systemic_risk"
};

export function parseWorldCopyFromText(worldText) {
  const playerWorld = documentSection(worldText, "player-world");
  const copySection = documentSection(worldText, "world-copy");

  const titleMatch = /^#\s+([^:]+):/m.exec(playerWorld);
  const title = titleMatch ? titleMatch[1].trim() : "Mandate 2038";

  // Parse Endings from player-world
  const endings = [];
  const endingMatches = [...playerWorld.matchAll(/###\s+([^\n]+)\r?\n\r?\n_Condition:\s*([^_]+)_\r?\n\r?\n([\s\S]+?)(?=\r?\n###|\r?\n<!--|$)/g)];
  for (const match of endingMatches) {
    const name = match[1].trim();
    const condition = match[2].trim();
    const text = match[3].trim();
    const meta = ENDING_METADATA[name];
    if (!meta) throw new Error(`Unknown ending name in world.md: "${name}"`);
    endings.push({
      id: meta.id,
      name,
      condition,
      text,
      $scenario: meta.$scenario
    });
  }
  if (endings.length !== 4) {
    throw new Error(`Expected 4 endings in world.md, found ${endings.length}`);
  }

  // Parse Token Copy and Box Copy from world-copy
  const tokenCopy = [];
  const tokenMatches = [...copySection.matchAll(/\*\s+\*\*([^*]+)\*\*:\s*([^\n]+)/g)];
  const box = {};
  for (const match of tokenMatches) {
    const key = match[1].trim();
    const value = match[2].trim();
    if (TOKEN_IDS[key]) {
      tokenCopy.push({
        id: TOKEN_IDS[key],
        name: key,
        microcopy: value
      });
    } else {
      const boxKeyMap = {
        "Front strapline": "frontStrapline",
        "Back copy": "backCopy",
        "Short pitch": "shortPitch",
        "Content warning": "contentWarning"
      };
      if (boxKeyMap[key]) {
        box[boxKeyMap[key]] = value;
      }
    }
  }

  if (tokenCopy.length !== 8) {
    throw new Error(`Expected 8 token items in world.md, found ${tokenCopy.length}`);
  }
  for (const requiredField of ["frontStrapline", "backCopy", "shortPitch", "contentWarning"]) {
    if (!box[requiredField]) {
      throw new Error(`Missing box copy field in world.md: ${requiredField}`);
    }
  }

  return {
    schemaVersion: 1,
    status: "draft_print_copy",
    tokenCopy,
    endings,
    title,
    box
  };
}

export function parseScenarioBacklog(worldText) {
  const section = documentSection(worldText, "scenario-backlog").trim();
  if (section.startsWith("```json")) {
    const match = /^```json\r?\n([\s\S]*)\r?\n```$/.exec(section);
    if (!match) throw new Error("Scenario backlog must be one JSON code block in world.md.");
    return JSON.parse(match[1]);
  }

  const scenarios = [];
  const blocks = section.split(/\r?\n(?=###\s+)/);
  for (const block of blocks) {
    if (!block.trim().startsWith("###")) continue;
    const lines = block.trim().split(/\r?\n/);
    const titleMatch = /^###\s+(?:(?:\d+[\.\)]\s+)?)(.+)$/.exec(lines[0]);
    const title = titleMatch ? titleMatch[1].trim() : "";
    const getField = (pattern) => {
      const line = lines.find(l => pattern.test(l));
      if (!line) return undefined;
      const m = line.match(/:\s*(.+)$/);
      return m ? m[1].trim() : undefined;
    };

    const id = getField(/\*\*(?:Id|ID)\*\*/i)?.replace(/`/g, "") || title.toLowerCase().replace(/[^a-z0-9]+/g, "-");
    const eraId = getField(/\*\*Era\*\*/i)?.toLowerCase();
    const disposition = getField(/\*\*Disposition\*\*/i) || "research-backlog";
    const conceptsStr = getField(/\*\*Concepts?\*\*/i) || title;
    const concepts = conceptsStr.split(",").map(s => s.trim()).filter(Boolean);
    const threadsStr = getField(/\*\*Causal threads?\*\*/i) || "";
    const causalThreadIds = threadsStr ? threadsStr.split(",").map(s => s.trim().replace(/`/g, "")).filter(Boolean) : [];
    const publicBenefit = getField(/\*\*Public benefit\*\*/i) || "";
    const institutionalConsequence = getField(/\*\*Institutional consequence\*\*/i) || "";
    const mechanicPreservationStr = getField(/\*\*Mechanic preservation\*\*/i) || "not-mapped";
    let status = "not-mapped";
    let summary = "No current component mechanic expresses this scenario cleanly.";
    if (mechanicPreservationStr.includes("(") && mechanicPreservationStr.includes(")")) {
      const m = mechanicPreservationStr.match(/^([^(]+)\((.+)\)$/);
      if (m) {
        status = m[1].trim();
        summary = m[2].trim();
      }
    } else if (mechanicPreservationStr) {
      status = mechanicPreservationStr.trim();
    }
    const deploymentProfilesStr = getField(/\*\*Deployment profiles?\*\*/i) || "internal-review";
    const deploymentProfiles = deploymentProfilesStr.split(",").map(s => s.trim()).filter(Boolean);

    scenarios.push({
      id,
      title,
      eraId,
      disposition,
      concepts,
      causalThreadIds,
      publicBenefit,
      institutionalConsequence,
      mechanicPreservation: { status, summary },
      deploymentProfiles
    });
  }
  return scenarios;
}

export async function readWorldDocument(worldPath = "world.md") {
  const text = await readFile(resolve(root, worldPath), "utf8");
  return {
    text,
    worldCopy: parseWorldCopyFromText(text),
    backlog: parseScenarioBacklog(text)
  };
}

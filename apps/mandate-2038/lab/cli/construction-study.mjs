import { readFile, writeFile, mkdir, open, rename, rm } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { createHash } from "node:crypto";
import { createSimulation } from "../runtime/create-simulation.js";
import { archiveSimulationReport } from "../report-archive.js";

const root = resolve(import.meta.dirname, "../..");
const sha = bytes => `sha256:${createHash("sha256").update(bytes).digest("hex")}`;

export async function loadCheckpoint(path, {root, mode, seed}) {
  const bytes = await readFile(path);
  const checkpoint = JSON.parse(bytes);
  if (checkpoint.mode !== mode || checkpoint.seed !== seed || checkpoint.complete || !Array.isArray(checkpoint.results)) throw new Error("Incompatible or completed study checkpoint.");
  const keys = new Set();
  for (const row of checkpoint.results) {
    const key = `${row.block}:${row.treatment}`;
    if (keys.has(key)) throw new Error("Duplicate checkpoint result.");
    keys.add(key);
    for (const [field, hashField] of [["report", "reportSha256"], ["outcomes", "outcomesSha256"]]) {
      const file = resolve(root, row[field]);
      if (!file.startsWith(resolve(root, "evidence/studies/simulation") + "/") || sha(await readFile(file)) !== row[hashField]) throw new Error("Checkpoint artifact hash mismatch.");
    }
  }
  return {results: checkpoint.results, parent: {path, sha256: sha(bytes)}};
}

async function runStudy(argv) {
const mode = argv[0] || "calibration";
if (!["calibration", "holdout", "personal"].includes(mode)) throw new Error("Use calibration, holdout, or personal.");
const seed = mode === "personal" ? "2038-construction-personal-20260908-v2" : `2038-construction-${mode}-20260906-${mode === "calibration" ? "v2" : "v1"}`;
const factions = JSON.parse(await readFile(resolve(root, "dist/runtime/factions.json"))).factions;
const arms = mode === "personal" ? ["personal_infrastructure_v1", "research_deploy_plan_v1"] : [null, "infrastructure_plan_v1", "research_deploy_plan_v1"];
const opponents = ["balanced_operator", "capability_rusher", "market_maximalist", "trust_governor"];
const blocks = [];
for (const count of mode === "calibration" ? [4] : [4, 2, 3, 5]) {
  for (const faction of factions.slice(0, mode === "calibration" ? 1 : 6)) {
    for (let seat = 0; seat < (count === 4 && mode === "holdout" ? 4 : 1); seat++) {
      for (const backend of ["greedy", "weighted"]) blocks.push({ count, faction: faction.id, seat: mode === "personal" ? factions.indexOf(faction) % count : seat, backend });
    }
  }
}
const directory = resolve(root, "evidence/studies/simulation");
await mkdir(directory, { recursive: true });
const resumePath = argv[1] === "--resume" && argv[2] ? resolve(argv[2]) : null;
if (argv.length > 1 && (!resumePath || argv.length !== 3)) throw new Error("Use: construction-study.mjs MODE [--resume CHECKPOINT].");
const resumed = resumePath ? await loadCheckpoint(resumePath, {root, mode, seed}) : {results: [], parent: null};
const destination = resolve(directory, `${seed}${resumed.parent ? '-resume-' + resumed.parent.sha256.slice(7,19) : ''}.json`);
// Never overwrite a previously inspected result under the same study identity.
await (await open(destination, "wx")).close();
const results = [...resumed.results];
const scheduled = new Set(blocks.flatMap((_block, index) => (mode === "personal" || _block.count === 4 ? arms : arms.slice(1)).map(arm => `${index}:${arm || 'baseline'}`)));
if (results.some(row => !scheduled.has(`${row.block}:${row.treatment}`))) throw new Error("Checkpoint includes an unscheduled result.");
async function checkpoint(complete, failure) {
  const temporary = `${destination}.tmp`;
  try {
    await writeFile(temporary, JSON.stringify({evidenceLabel: "simulation", mode, seed, complete, parent: resumed.parent, ...(failure ? {failure} : {}), results}, null, 2), {flag: "wx"});
    await rename(temporary, destination);
  } finally {await rm(temporary, {force: true});}
}
await checkpoint(false);
try {
  for (const [blockIndex, block] of blocks.entries()) {
    const { count, faction, seat, backend } = block;
    const factionIds = factions.filter(candidate => candidate.id !== faction).map(candidate => candidate.id).slice(0, count - 1);
    factionIds.splice(seat, 0, faction);
    const profileIds = Array.from({ length: count - 1 }, (_, index) => opponents[index]);
    profileIds.splice(seat, 0, "infrastructure_compounder");
    for (const treatment of mode === "personal" || count === 4 ? arms : arms.slice(1)) {
      const policyTreatments = Array(count).fill(null);
      policyTreatments[seat] = treatment;
      const options = { runs: 1, playerCount: count, seed: `${seed}-block-${blockIndex}`,
        factionIds, profileIds, backends: Array(count).fill(backend), policyTreatments,
        rotateFactions: false, rotateProfiles: false, mandateMode: "variable",
        simulateNegotiation: true, rulesVariant: {}, sampleReplays: 0,
        returnOutcomes: true, projection: "rich" };
      const prior = results.find(row => row.block === blockIndex && row.treatment === (treatment || 'baseline'));
      if (prior) {
        if (JSON.stringify(prior.options) !== JSON.stringify(options)) throw new Error("Checkpoint options differ from the scheduled comparison.");
        continue;
      }
      const { report, outcomes } = await createSimulation(options);
      if (results.length && (results[0].game.rulesetFingerprint !== report.game.rulesetFingerprint || results[0].engine.fingerprint !== report.engine.fingerprint)) throw new Error("Resumed study identity differs from the retained game or engine.");
      if (mode === "personal" && report.provenance.sourceDirty) throw new Error("Personal project comparison requires a clean committed source.");
      const archive = await archiveSimulationReport(report, { projectRoot: root, jobId: treatment || "baseline" });
      const reportBytes = await readFile(resolve(root, archive.relativePath));
      const outcomePath = archive.relativePath.replace(/\.json$/, "-outcomes.json");
      const outcomeBytes = `${JSON.stringify(outcomes)}\n`;
      await writeFile(resolve(root, outcomePath), outcomeBytes, { flag: "wx" });
      const outcome = outcomes[0].outcome;
      const focal = outcome.standings.find(player => player.seat === seat);
      const production = outcome.matchMetrics.projectProduction.filter(event => event.seat === seat);
      results.push({ block: blockIndex, ...block, treatment: treatment || "baseline",
        options, report: archive.relativePath, reportSha256: sha(reportBytes),
        outcomes: outcomePath, outcomesSha256: sha(outcomeBytes),
        score: focal.score, winShare: outcome.winnerSeats.includes(seat) ? 1 / outcome.winnerSeats.length : 0,
        projects: focal.metrics.projects, construction: focal.metrics.construction,
        firstProductiveProjectEra: production[0]?.round ?? null,
        productiveProjectEras: new Set(production.map(event => event.round)).size,
        projectProduction: production,
        projectCapabilityGained: production.filter(event => event.resource === "capability").reduce((sum, event) => sum + event.gained, 0),
        projectComputeGained: production.filter(event => event.resource === "compute").reduce((sum, event) => sum + event.gained, 0),
        agiDeclared: focal.agiDeclared, actions: focal.metrics.actions,
        capability: focal.capability, customers: focal.customers, trust: focal.trust,
        poweredFacilities: focal.poweredFacilityMandate, worldEnding: outcome.worldEnding.id,
        productions: outcome.matchMetrics.productionSnapshots.length,
        game: report.game, engine: report.engine });
      await checkpoint(false);
      process.stdout.write(`${results.length}: ${count}p ${faction} seat ${seat + 1} ${backend} ${treatment || "baseline"}: score ${focal.score}, projects ${JSON.stringify(focal.metrics.projects)}, first production ${production[0]?.round ?? "none"}\n`);
    }

  }
  await checkpoint(true);
  process.stdout.write(`${destination}\n`);
} catch (error) {
  await checkpoint(false, {code: error.code || null, message: error.message}).catch(() => {});
  throw error;
}
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) await runStudy(process.argv.slice(2));

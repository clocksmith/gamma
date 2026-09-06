import { readFile, writeFile, mkdir } from "node:fs/promises";
import { resolve } from "node:path";
import { createHash } from "node:crypto";
import { createSimulation } from "../runtime/create-simulation.js";
import { archiveSimulationReport } from "../report-archive.js";

const root = resolve(import.meta.dirname, "../..");
const mode = process.argv[2] || "calibration";
if (!["calibration", "holdout"].includes(mode)) throw new Error("Use calibration or holdout.");
const seed = `2038-construction-${mode}-20260906-${mode === "calibration" ? "v2" : "v1"}`;
const factions = JSON.parse(await readFile(resolve(root, "dist/runtime/factions.json"))).factions;
const arms = [null, "infrastructure_plan_v1", "research_deploy_plan_v1"];
const opponents = ["balanced_operator", "capability_rusher", "market_maximalist", "trust_governor"];
const blocks = [];
for (const count of mode === "calibration" ? [4] : [4, 2, 3, 5]) {
  for (const faction of factions.slice(0, mode === "calibration" ? 1 : 6)) {
    for (let seat = 0; seat < (count === 4 && mode === "holdout" ? 4 : 1); seat++) {
      for (const backend of ["greedy", "weighted"]) blocks.push({ count, faction: faction.id, seat, backend });
    }
  }
}
const directory = resolve(root, "evidence/studies/simulation");
await mkdir(directory, { recursive: true });
const destination = resolve(directory, `${seed}.json`);
// Never overwrite a previously inspected result under the same study identity.
const output = await import("node:fs/promises").then(fs => fs.open(destination, "wx"));
const sha = bytes => `sha256:${createHash("sha256").update(bytes).digest("hex")}`;
const results = [];
try {
  for (const [blockIndex, block] of blocks.entries()) {
    const { count, faction, seat, backend } = block;
    const factionIds = factions.filter(candidate => candidate.id !== faction).map(candidate => candidate.id).slice(0, count - 1);
    factionIds.splice(seat, 0, faction);
    const profileIds = Array.from({ length: count - 1 }, (_, index) => opponents[index]);
    profileIds.splice(seat, 0, "infrastructure_compounder");
    for (const treatment of count === 4 ? arms : arms.slice(1)) {
      const policyTreatments = Array(count).fill(null);
      policyTreatments[seat] = treatment;
      const options = { runs: 1, playerCount: count, seed: `${seed}-block-${blockIndex}`,
        factionIds, profileIds, backends: Array(count).fill(backend), policyTreatments,
        rotateFactions: false, rotateProfiles: false, mandateMode: "variable",
        simulateNegotiation: true, rulesVariant: {}, sampleReplays: 0,
        returnOutcomes: true, projection: "rich" };
      const { report, outcomes } = await createSimulation(options);
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
        productiveProjectEras: production.length,
        projectComputeGained: production.reduce((sum, event) => sum + event.gainedCompute, 0),
        agiDeclared: focal.agiDeclared, actions: focal.metrics.actions,
        capability: focal.capability, customers: focal.customers, trust: focal.trust,
        poweredFacilities: focal.poweredFacilityMandate, worldEnding: outcome.worldEnding.id,
        productions: outcome.matchMetrics.productionSnapshots.length,
        game: report.game, engine: report.engine });
      process.stdout.write(`${results.length}: ${count}p ${faction} seat ${seat + 1} ${backend} ${treatment || "baseline"}: score ${focal.score}, projects ${JSON.stringify(focal.metrics.projects)}, first production ${production[0]?.round ?? "none"}\n`);
    }
    await output.truncate(0);
    await output.write(JSON.stringify({ evidenceLabel: "simulation", mode, seed, complete: false, results }, null, 2), 0, "utf8");
  }
  await output.truncate(0);
  await output.write(JSON.stringify({ evidenceLabel: "simulation", mode, seed, complete: true, results }, null, 2), 0, "utf8");
  process.stdout.write(`${destination}\n`);
} finally { await output.close(); }

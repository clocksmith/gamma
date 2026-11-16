import { createHash } from "node:crypto";
import { readFile, writeFile, mkdir, open, rename, rm } from "node:fs/promises";
import { resolve } from "node:path";
import { createSimulation } from "../../lab/runtime/create-simulation.js";
import { archiveSimulationReport } from "../../lab/report-archive.js";
import { loadCheckpoint } from "../../lab/cli/construction-study.mjs";

const root = resolve(import.meta.dirname, "../..");
const mode = "personal-current-4p";
const seed = "2038-construction-personal-20260923-v1";
const treatments = ["personal_infrastructure_v1", "research_deploy_plan_v1"];
const rivals = ["balanced_operator", "capability_rusher", "market_maximalist"];
const sha = bytes => `sha256:${createHash("sha256").update(bytes).digest("hex")}`;
const factions = JSON.parse(await readFile(resolve(root, "dist/runtime/factions.json"))).factions;
const blocks = factions.flatMap(faction =>
  Array.from({ length: 4 }, (_, seat) => seat).flatMap(seat =>
    ["greedy", "weighted"].map(backend => ({ faction: faction.id, seat, backend }))
  )
);
const archiveRoot = resolve(root, "evidence/studies/simulation");
await mkdir(archiveRoot, { recursive: true });

const args = process.argv.slice(2);
if (args.length && (args.length !== 2 || args[0] !== "--resume")) {
  throw new Error("Use: node evidence/studies/2026-09-23-personal-infrastructure-4p.mjs [--resume CHECKPOINT]");
}
const resumed = args.length
  ? await loadCheckpoint(resolve(args[1]), { root, mode, seed })
  : { results: [], parent: null };
const destination = resolve(archiveRoot,
  `${seed}${resumed.parent ? `-resume-${resumed.parent.sha256.slice(7, 19)}` : ""}.json`
);
await (await open(destination, "wx")).close();
const results = [...resumed.results];
const scheduled = new Set(blocks.flatMap((_, block) =>
  treatments.map(treatment => `${block}:${treatment}`)
));
if (results.some(row => !scheduled.has(`${row.block}:${row.treatment}`))) {
  throw new Error("Checkpoint contains an unscheduled comparison.");
}

async function checkpoint(complete, failure) {
  const temporary = `${destination}.tmp`;
  try {
    await writeFile(temporary, `${JSON.stringify({
      evidenceLabel: "simulation",
      mode,
      seed,
      complete,
      parent: resumed.parent,
      ...(failure ? { failure } : {}),
      contract: {
        playerCount: 4,
        factions: factions.map(faction => faction.id),
        seats: [0, 1, 2, 3],
        backends: ["greedy", "weighted"],
        treatments,
        rivals,
        rulesVariant: {},
        mandateMode: "variable",
        simulateNegotiation: true
      },
      results
    }, null, 2)}\n`, { flag: "wx" });
    await rename(temporary, destination);
  } finally {
    await rm(temporary, { force: true });
  }
}

await checkpoint(false);
try {
  for (const [block, { faction, seat, backend }] of blocks.entries()) {
    const factionIds = factions.filter(candidate => candidate.id !== faction)
      .slice(0, 3).map(candidate => candidate.id);
    factionIds.splice(seat, 0, faction);
    const profileIds = [...rivals];
    profileIds.splice(seat, 0, "infrastructure_compounder");
    for (const treatment of treatments) {
      const policyTreatments = Array(4).fill(null);
      policyTreatments[seat] = treatment;
      const options = {
        runs: 1,
        playerCount: 4,
        seed: `${seed}-block-${block}`,
        factionIds,
        profileIds,
        backends: Array(4).fill(backend),
        policyTreatments,
        rotateFactions: false,
        rotateProfiles: false,
        mandateMode: "variable",
        simulateNegotiation: true,
        rulesVariant: {},
        sampleReplays: 0,
        returnOutcomes: true,
        projection: "rich"
      };
      const prior = results.find(row => row.block === block && row.treatment === treatment);
      if (prior) {
        if (JSON.stringify(prior.options) !== JSON.stringify(options)) {
          throw new Error("Checkpoint options differ from this comparison.");
        }
        continue;
      }
      const { report, outcomes } = await createSimulation(options);
      if (report.provenance.sourceDirty) throw new Error("Comparison requires clean committed source.");
      if (results.length && (results[0].game.rulesetFingerprint !== report.game.rulesetFingerprint ||
        results[0].engine.fingerprint !== report.engine.fingerprint)) {
        throw new Error("Game or engine identity drifted during the comparison.");
      }
      const archive = await archiveSimulationReport(report, { projectRoot: root, jobId: treatment });
      const reportBytes = await readFile(resolve(root, archive.relativePath));
      const outcomesPath = archive.relativePath.replace(/\.json$/, "-outcomes.json");
      const outcomesBytes = `${JSON.stringify(outcomes)}\n`;
      await writeFile(resolve(root, outcomesPath), outcomesBytes, { flag: "wx" });
      const outcome = outcomes[0].outcome;
      const focal = outcome.standings.find(player => player.seat === seat);
      const production = outcome.matchMetrics.projectProduction.filter(event => event.seat === seat);
      results.push({
        block, playerCount: 4, faction, seat, backend, treatment, options,
        report: archive.relativePath, reportSha256: sha(reportBytes),
        outcomes: outcomesPath, outcomesSha256: sha(outcomesBytes),
        score: focal.score,
        winShare: outcome.winnerSeats.includes(seat) ? 1 / outcome.winnerSeats.length : 0,
        projects: focal.metrics.projects,
        construction: focal.metrics.construction,
        projectProduction: production,
        agiDeclared: focal.agiDeclared,
        game: report.game,
        engine: report.engine,
        provenance: report.provenance
      });
      await checkpoint(false);
      process.stdout.write(`${results.length}/96: ${faction} seat ${seat + 1} ${backend} ${treatment} score ${focal.score}\n`);
    }
  }
  await checkpoint(true);
  process.stdout.write(`${destination}\n`);
} catch (error) {
  await checkpoint(false, { code: error.code || null, message: error.message }).catch(() => {});
  throw error;
}

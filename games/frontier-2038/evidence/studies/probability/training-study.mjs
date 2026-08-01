import { mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { simulateTrainingRun } from "../../prototype/src/engine.js";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const config = JSON.parse(await readFile(resolve(projectRoot, "data/game-config.json"), "utf8"));
const runsPerPolicy = Number(process.env.FRONTIER_STUDY_RUNS || 10000);
const policies = [];

for (const safety of [0, 1]) {
  for (const stopAt of [2, 3, 4, 5, 6, 7]) {
    const outcomes = new Map();
    let capability = 0;
    let scrutiny = 0;
    let cards = 0;
    for (let run = 0; run < runsPerPolicy; run += 1) {
      const result = simulateTrainingRun(config, `study:${safety}:${stopAt}:${run}`, {
        stopAt,
        runway: 12,
        safety
      });
      capability += result.capability;
      scrutiny += result.scrutiny;
      cards += result.revealed.length;
      outcomes.set(result.outcome, (outcomes.get(result.outcome) || 0) + 1);
    }
    policies.push({
      safety,
      stopAt,
      runs: runsPerPolicy,
      meanCapability: capability / runsPerPolicy,
      meanScrutiny: scrutiny / runsPerPolicy,
      meanCardsRevealed: cards / runsPerPolicy,
      outcomes: Object.fromEntries([...outcomes].sort())
    });
  }
}

const report = {
  schemaVersion: 1,
  generatedAt: new Date().toISOString(),
  rules: {
    trainingCards: config.trainingDeck.cards.reduce((sum, card) => sum + card.count, 0),
    domains: config.trainingDeck.cards.filter((card) => card.kind === "domain").length,
    note: "Simulation evidence only. This is not a human playtest or balance verdict."
  },
  policies
};

const output = resolve(projectRoot, "studies/probability/training-study.latest.json");
await mkdir(dirname(output), { recursive: true });
await writeFile(output, `${JSON.stringify(report, null, 2)}\n`);
process.stdout.write(`${output}\n`);

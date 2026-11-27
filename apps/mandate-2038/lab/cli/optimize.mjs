import { readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { stderr, stdout } from "node:process";
import { runExperiment } from "../runtime/run-experiment.js";

function parseArguments(values) {
  const options = {};
  for (let index = 0; index < values.length; index += 1) {
    const argument = values[index];
    if (!argument.startsWith("--")) throw new TypeError(`Unexpected argument: ${argument}`);
    const value = values[index + 1];
    if (value === undefined || value.startsWith("--")) {
      throw new TypeError(`Missing value for ${argument}.`);
    }
    options[argument.slice(2)] = value;
    index += 1;
  }
  return options;
}

const input = parseArguments(process.argv.slice(2));
const profileOverrideArtifacts = input["profile-override-reports"]
  ? await Promise.all(
    input["profile-override-reports"].split(",").filter(Boolean).map(async (path) => {
      const contents = await readFile(path);
      const report = JSON.parse(contents);
      if (!report.championProfile) {
        throw new TypeError(`Evolution report ${path} has no championProfile.`);
      }
      return {
        profile: report.championProfile,
        source: {
          path,
          profileId: report.championProfile.id,
          sha256: createHash("sha256").update(contents).digest("hex")
        }
      };
    })
  )
  : [];
const report = await runExperiment({
  mode: input.mode || "strategy-evolution",
  seed: input.seed,
  playerCount: input.players,
  playerCounts: input["player-counts"],
  runs: input.runs,
  runsPerSeat: input["runs-per-seat"],
  targetProfileId: input.profile,
  generations: input.generations,
  population: input.population,
  magnitude: input.magnitude,
  backendId: input.backend,
  targetWinShare: input["target-win-share"],
  opponentCoverage: input["opponent-coverage"],
  profileOverrides: profileOverrideArtifacts.map((entry) => entry.profile),
  profileOverrideSources: profileOverrideArtifacts.map((entry) => entry.source),
  iterations: input.iterations,
  targetAgiRate: input["target-agi-rate"],
  profileIds: input.profiles?.split(",").filter(Boolean)
}, ({ phase, completed, total }) => {
  stderr.write(`${phase} ${completed}/${total}\n`);
});

const serialized = `${JSON.stringify(report, null, 2)}\n`;
if (input.output) {
  await writeFile(input.output, serialized);
  stdout.write(`${input.output}\n`);
} else {
  stdout.write(serialized);
}

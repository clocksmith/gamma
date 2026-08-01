#!/usr/bin/env node
import { writeFile } from "node:fs/promises";
import { runBalanceAudit } from "../runner/balance-audit-runner.js";

function argumentsMap(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 1) {
    if (!argv[index].startsWith("--")) continue;
    const key = argv[index].slice(2);
    result[key] = argv[index + 1]?.startsWith("--") ? true : argv[++index] ?? true;
  }
  return result;
}

const args = argumentsMap(process.argv.slice(2));
const report = await runBalanceAudit({
  runsPerMatchup: Number(args.runs || args["runs-per-matchup"] || 8),
  generations: Number(args.generations || 2),
  population: Number(args.population || 3),
  seed: args.seed || "m3t4-balance-audit",
  magnitude: args.magnitude === undefined ? undefined : Number(args.magnitude),
  onProgress: ({ phase, completed, total }) => {
    process.stderr.write(`\r${phase}: ${completed}/${total}`);
  }
});
process.stderr.write("\n");
const output = `${JSON.stringify(report, null, 2)}\n`;
if (args.output) {
  await writeFile(args.output, output);
  console.log(args.output);
} else {
  process.stdout.write(output);
}

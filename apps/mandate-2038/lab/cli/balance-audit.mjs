#!/usr/bin/env node
import { writeFile } from "node:fs/promises";
import { runBalanceAudit } from "../runner/balance-audit-runner.js";

const allowed = new Set('runs runs-per-matchup generations population seed magnitude output'.split(' '));
if (process.argv.includes('--help')) {
  console.log('Options (each takes a value): ' + [...allowed].map(key => '--' + key).join(', '));
  process.exit(0);
}
function argumentsMap(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 1) {
    if (!argv[index].startsWith("--")) throw new TypeError(`Unexpected argument: ${argv[index]}`);
    const key = argv[index].slice(2);
    if (!allowed.has(key)) throw new TypeError(`Unknown option: --${key}`);
    if (!argv[index + 1] || argv[index + 1].startsWith("--")) throw new TypeError(`Missing value: --${key}`);
    result[key] = argv[index + 1]?.startsWith("--") ? true : argv[++index] ?? true;
  }
  return result;
}

const args = argumentsMap(process.argv.slice(2));
const report = await runBalanceAudit({
  runsPerMatchup: Number(args.runs || args["runs-per-matchup"] || 8),
  generations: Number(args.generations || 2),
  population: Number(args.population || 3),
  seed: args.seed || "mandate-2038-balance-audit",
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

#!/usr/bin/env node

import process from 'node:process';
import { pathToFileURL } from 'node:url';

import { verifyStudentCodeExperimentContracts } from './lib/student-code-experiment.js';

function parseArgs(argv) {
  const options = {
    json: false,
    policyPath: null,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--json') {
      options.json = true;
      continue;
    }
    if (arg === '--policy') {
      options.policyPath = String(argv[index + 1] || '');
      index += 1;
      continue;
    }
    throw new Error(`Unknown argument: ${arg}`);
  }
  return options;
}

export async function main(argv = process.argv.slice(2)) {
  const options = parseArgs(argv);
  const report = await verifyStudentCodeExperimentContracts({
    policyPath: options.policyPath || undefined,
  });
  if (options.json) {
    console.log(JSON.stringify(report, null, 2));
  } else if (report.ok) {
    console.log(
      `student-code-experiment: ok (${report.holdoutTasks} holdouts, `
      + `${report.adapters.length} adapters, release ${report.releaseTarget})`
    );
  } else {
    for (const error of report.errors) {
      console.error(`student-code-experiment: ${error}`);
    }
  }
  if (!report.ok) process.exitCode = 1;
  return report;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    console.error(error?.stack || error?.message || String(error));
    process.exitCode = 1;
  });
}

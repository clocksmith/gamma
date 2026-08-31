import { resolve } from "node:path";
import {
  ledgerPath,
  validateEraSituationLedger
} from "./era-situation-ledger.mjs";

const projectRoot = resolve(import.meta.dirname, "../..");
const result = await validateEraSituationLedger({ root: projectRoot });

process.stdout.write(
  `era-situation-ledger: verified ${result.eras} Eras, ` +
  `${result.scenarios} scenarios, ${result.surfaces} unique surfaces, ` +
  `${result.profiles} publication profiles from ${ledgerPath}\n`
);

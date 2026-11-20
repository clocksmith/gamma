#!/usr/bin/env node
// Record a person's verdict on one arm's diagnosis beside its mechanical checks. The trial report
// is never rewritten: the grade goes to a sibling file that names the report it was read from.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { gradeDiagnosis } from './authenticated-investigation-judge.js';
import { sha256Hex } from '../src/journal.js';

const help = 'Usage: node projects/workspace/qualification/authenticated-investigation-grade.js --report FILE --arm NAME --correct true|false --graded-by WHO --basis TEXT';
const args = process.argv.slice(2), value = flag => { const i = args.indexOf(flag); return i < 0 ? null : args[i + 1]; };
if (args.includes('--help')) { console.log(help); process.exit(0); }
const file = value('--report'), arm = value('--arm'), correct = value('--correct');
if (!file || !arm || !['true', 'false'].includes(correct)) throw Error(help);
const bytes = readFileSync(resolve(file), 'utf8'), report = JSON.parse(bytes);
const row = report.rows.find(candidate => candidate.arm === arm);
if (!row?.verdict) throw Error(`No judged arm named ${arm}; arms are ${report.rows.map(candidate => candidate.arm).join(', ')}`);
const out = join(dirname(resolve(file)), `diagnosis-grade-${arm}.json`);
if (existsSync(out)) throw Error('This arm is already graded; a grade is never overwritten');
const graded = gradeDiagnosis(row.verdict, { correct: correct === 'true', gradedBy: value('--graded-by'), basis: value('--basis') });
writeFileSync(out, `${JSON.stringify({ schemaVersion: 1, report: resolve(file), reportSha256: sha256Hex(bytes), arm,
  mechanicallyAccepted: graded.mechanicallyAccepted, diagnosis: graded.diagnosis, accepted: graded.accepted }, null, 2)}\n`);
console.log(JSON.stringify({ arm, accepted: graded.accepted, diagnosis: graded.diagnosis, written: out }));

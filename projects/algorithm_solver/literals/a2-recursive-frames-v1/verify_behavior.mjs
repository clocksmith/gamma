#!/usr/bin/env node
/**
 * Execute frozen JavaScript behavior checks (from checks.py) comparing
 * normalized/decoded JS against original JS inside isolated vm contexts.
 *
 * Input (JSON on stdin):
 *   {
 *     "programs": [
 *       {
 *         "id": "0121",
 *         "method": "maxProfit",
 *         "interface": "solution-class", // or "function"
 *         "original_source": "...",
 *         "candidate_source": "...",
 *         "cases": [ { "args": [...] }, ... ]
 *       }
 *     ]
 *   }
 *
 * Output (JSON on stdout):
 *   Per-program and aggregate pass/fail counts, keeping every failure or
 *   unsupported program in the denominator.
 */
import fs from 'node:fs';
import vm from 'node:vm';

function runSource(source, iface, method, cases) {
  const ctx = vm.createContext({});
  vm.runInContext(source, ctx, { filename: 'program.js', timeout: 2000 });
  const target = vm.runInContext(iface === 'function' ? 'solve' : 'Solution', ctx, { timeout: 1000 });
  const records = [];
  for (let i = 0; i < cases.length; i++) {
    const args = JSON.parse(JSON.stringify(cases[i].args));
    const argsBefore = JSON.parse(JSON.stringify(args));
    try {
      const result = iface === 'function' ? target(...args) : new target()[method](...args);
      records.push({ i, ok: true, result, args_before: argsBefore, args_after: args });
    } catch (err) {
      records.push({ i, ok: false, error: String(err), args_before: argsBefore, args_after: args });
    }
  }
  return records;
}

function stableJson(v) {
  return JSON.stringify(v);
}

const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const rows = [];
let totalPrograms = 0;
let passedPrograms = 0;
let totalCases = 0;
let passedCases = 0;

for (const prog of input.programs) {
  totalPrograms++;
  totalCases += prog.cases.length;
  try {
    const orig = runSource(prog.original_source, prog.interface, prog.method, prog.cases);
    const cand = runSource(prog.candidate_source, prog.interface, prog.method, prog.cases);
    let matches = 0;
    const mismatches = [];
    for (let i = 0; i < prog.cases.length; i++) {
      const same =
        orig[i].ok === cand[i].ok &&
        stableJson(orig[i].result) === stableJson(cand[i].result) &&
        stableJson(orig[i].args_after) === stableJson(cand[i].args_after) &&
        orig[i].error === cand[i].error;
      if (same) {
        matches++;
      } else if (mismatches.length < 5) {
        mismatches.push({ i, orig: orig[i], cand: cand[i] });
      }
    }
    const allPass = matches === prog.cases.length;
    if (allPass) passedPrograms++;
    passedCases += matches;
    rows.push({
      id: prog.id,
      method: prog.method,
      total_cases: prog.cases.length,
      matched_cases: matches,
      all_passed: allPass,
      mismatches,
      error: null,
    });
  } catch (err) {
    rows.push({
      id: prog.id,
      method: prog.method,
      total_cases: prog.cases.length,
      matched_cases: 0,
      all_passed: false,
      mismatches: [],
      error: String(err && err.message ? err.message : err),
    });
  }
}

process.stdout.write(JSON.stringify({
  total_programs: totalPrograms,
  passed_programs: passedPrograms,
  total_cases: totalCases,
  passed_cases: passedCases,
  all_passed: passedPrograms === totalPrograms && passedCases === totalCases,
  rows,
}, null, 2) + '\n');

'use strict';

// 618. Students Report By Geography. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. student: name, continent in America/Asia/Europe. Output columns: America, Asia, Europe, with names independently alphabetized and NULL padding.

function solve(student) {
  const groups = {America: [], Asia: [], Europe: []};
  for (const row of student) groups[row.continent].push(row.name);
  for (const names of Object.values(groups)) names.sort();
  const height = Math.max(groups.America.length, groups.Asia.length, groups.Europe.length);
  return Array.from({length: height}, (_, i) => ({America: groups.America[i] ?? null, Asia: groups.Asia[i] ?? null, Europe: groups.Europe[i] ?? null}));
}

const geographyReport = solve;
class Solution {
  geographyReport(student) { return solve(student); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, geographyReport };

'use strict';

// 574. Winning Candidate. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. candidate: id, name; vote: id, candidateId. Output: name. The statement guarantees a unique winner.

function solve(candidate, vote) {
  const counts = new Map();
  for (const row of vote) counts.set(row.candidateId, (counts.get(row.candidateId) || 0) + 1);
  if (counts.size === 0) return [];
  let winner = null;
  for (const [id, count] of counts) {
    if (winner === null || count > counts.get(winner) || (count === counts.get(winner) && id < winner)) winner = id;
  }
  return candidate.filter(row => row.id === winner).map(row => ({name: row.name}));
}

const winningCandidate = solve;
class Solution {
  winningCandidate(candidate, vote) { return solve(candidate, vote); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, winningCandidate };

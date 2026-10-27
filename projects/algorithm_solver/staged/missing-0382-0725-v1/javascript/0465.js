'use strict';

// 465. Optimal Account Balancing. Backtrack over nonzero net balances, merging opposite signs.

function solve(transactions) {
  const balances = new Map();
  for (const [source, target, amount] of transactions) {
    balances.set(source, (balances.get(source) || 0) - amount);
    balances.set(target, (balances.get(target) || 0) + amount);
  }
  const remaining = Array.from(balances.values()).filter(value => value !== 0);
  function settle(start) {
    while (start < remaining.length && remaining[start] === 0) start += 1;
    if (start === remaining.length) return 0;
    let answer = remaining.length;
    const tried = new Set(), first = remaining[start];
    for (let i = start + 1; i < remaining.length; i += 1) {
      const other = remaining[i];
      if (first * other >= 0 || tried.has(other)) continue;
      tried.add(other); remaining[i] += first;
      answer = Math.min(answer, 1 + settle(start + 1));
      remaining[i] = other;
      if (other + first === 0) break;
    }
    return answer;
  }
  return settle(0);
}

const minTransfers = solve;
class Solution {
  minTransfers(transactions) { return solve(transactions); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minTransfers };

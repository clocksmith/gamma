/**
 * 4005. Minimum Operations to Make Array Equal III
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-operations-to-make-array-equal-iii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4005.Minimum%20Operations%20to%20Make%20Array%20Equal%20III/README_EN.md
 * Complexity: O(n + U*log M) expected time, O(U) space; M=max(nums), U=distinct values.
 * A new common multiple gives n operations. An improving existing target t>1 must have frequency(t)>count(incomparable values). Cancel incomparable pairs; every improving target survives in a divisibility chain of at most floor(log2 M)+1 values. Direct comparable changes cost one, incomparable changes two via a common multiple. Division to 1 is forbidden. Native method unconfirmed.
 */

function solve(nums) {
  const frequencies = new Map();
  for (const value of nums) frequencies.set(value, (frequencies.get(value) || 0) + 1);
  if (frequencies.size === 1) return 0;
  const survivors = new Map();
  for (const [value, count] of frequencies) {
    let amount = count;
    while (amount > 0) {
      let conflict = null;
      for (const other of survivors.keys()) if (value % other !== 0 && other % value !== 0) { conflict = other; break; }
      if (conflict === null) { survivors.set(value, (survivors.get(value) || 0) + amount); break; }
      const removed = Math.min(amount, survivors.get(conflict));
      amount -= removed;
      const remaining = survivors.get(conflict) - removed;
      if (remaining) survivors.set(conflict, remaining); else survivors.delete(conflict);
    }
  }
  const n = nums.length;
  let answer = n;
  for (const target of survivors.keys()) {
    if (target === 1) continue;
    let cost = n - frequencies.get(target);
    for (const [value, amount] of frequencies) if (target % value !== 0 && value % target !== 0) {
      cost += amount; if (cost >= answer) break;
    }
    answer = Math.min(answer, cost);
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}

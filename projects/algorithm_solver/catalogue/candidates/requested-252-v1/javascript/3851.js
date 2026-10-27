/**
 * 3851. Maximum Requests Without Violating the Limit
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(requests, k, window).
 * Algorithm: Per-user sorted greedy retention with a queue of retained requests in the inclusive window.
 * Complexity: O(n log n) time; O(n) space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/maximum-requests-without-violating-the-limit/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3851.Maximum%20Requests%20Without%20Violating%20the%20Limit/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: Duplicate requests count separately. Requests exactly window apart remain in the same closed interval.
 */

function solve(requests, k, window) {
  const byUser = new Map();
  for (const [user, time] of requests) {
    if (!byUser.has(user)) byUser.set(user, []);
    byUser.get(user).push(time);
  }
  let total = 0;
  for (const times of byUser.values()) {
    times.sort((a, b) => a - b);
    const kept = [];
    let head = 0;
    for (const time of times) {
      while (head < kept.length && time - kept[head] > window) head += 1;
      if (kept.length - head < k) {
        kept.push(time);
        total += 1;
      }
    }
  }
  return total;
}

function maxRequests(requests, k, window) {
  return solve(requests, k, window);
}

class Solution {
  maxRequests(requests, k, window) {
    return solve(requests, k, window);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, maxRequests, Solution };
}

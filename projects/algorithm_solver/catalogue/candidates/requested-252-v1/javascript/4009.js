/**
 * 4009. Minimum Possible Maximum Waiting Time
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-possible-maximum-waiting-time/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4009.Minimum%20Possible%20Maximum%20Waiting%20Time/README_EN.md
 * Complexity: O(n*F*D^2) time, O(F*D^2) space, F<=50 and D<=20.
 * Layered DP maximizes served prefix before minimizing maximum wait. Residual busy times are relative to the previous start, not absolute arrival zero. One fuel coordinate follows from consumed prefix demand. Inputs preserved; native method unconfirmed.
 */

function solve(demand, fuel) {
  const base = 21;
  const encode = (used, a, b) => (used * base + a) * base + b;
  let states = new Map([[0, 0]]), consumed = 0, served = 0;
  for (const amount of demand) {
    const following = new Map();
    const retain = (key, cost) => { if (!following.has(key) || cost < following.get(key)) following.set(key, cost); };
    for (const [state, worst] of states) {
      const busy1 = state % base, busy0 = Math.floor(state / base) % base, used0 = Math.floor(state / (base * base));
      const used1 = consumed - used0;
      if (used0 + amount <= fuel[0]) retain(encode(used0 + amount, amount, Math.max(0, busy1 - busy0)), Math.max(worst, busy0));
      if (used1 + amount <= fuel[1]) retain(encode(used0, Math.max(0, busy0 - busy1), amount), Math.max(worst, busy1));
    }
    if (following.size === 0) break;
    states = following; consumed += amount; served++;
  }
  if (!served) return -1;
  let answer = Infinity;
  for (const cost of states.values()) answer = Math.min(answer, cost);
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}

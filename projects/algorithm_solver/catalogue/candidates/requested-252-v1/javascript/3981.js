/**
 * 3981. Count Distinct Ways to Form Target from Two Strings
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-distinct-ways-to-form-target-from-two-strings/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3981.Count%20Distinct%20Ways%20to%20Form%20Target%20from%20Two%20Strings/README_EN.md
 * Complexity: O(|target|*|word1|*|word2|) time, O(|word1|*|word2|) space.
 * State records last selected index independently in each word; 0 means unused. Final states exclude both unused boundaries. No skip-path overcounting; inputs preserved. Native method unconfirmed.
 */

function solve(word1, word2, target) {
  const mod = 1000000007, m = word1.length, n = word2.length;
  let ways = Array.from({length: m + 1}, () => new Float64Array(n + 1));
  ways[0][0] = 1;
  for (const ch of target) {
    const following = Array.from({length: m + 1}, () => new Float64Array(n + 1));
    for (let j = 0; j <= n; j++) {
      let prefix = 0;
      for (let i = 1; i <= m; i++) {
        prefix = (prefix + ways[i - 1][j]) % mod;
        if (word1[i - 1] === ch) following[i][j] = prefix;
      }
    }
    for (let i = 0; i <= m; i++) {
      let prefix = 0;
      for (let j = 1; j <= n; j++) {
        prefix = (prefix + ways[i][j - 1]) % mod;
        if (word2[j - 1] === ch) following[i][j] = (following[i][j] + prefix) % mod;
      }
    }
    ways = following;
  }
  let answer = 0;
  for (let i = 1; i <= m; i++) for (let j = 1; j <= n; j++) answer = (answer + ways[i][j]) % mod;
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}

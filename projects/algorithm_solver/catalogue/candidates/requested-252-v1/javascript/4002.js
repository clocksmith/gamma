/**
 * 4002. Count Valid Sequences
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-valid-sequences/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4002.Count%20Valid%20Sequences/README_EN.md
 * Complexity: O(n+log MOD) time, O(n) space.
 * All positive compositions minus all-odd compositions. Exact split multiplication for modular products; native method unconfirmed.
 */

function multiplyMod(a, b, modulus = 1000000007) {
  const low = a % 32768, high = Math.floor(a / 32768);
  return (low * b + ((high * b) % modulus) * 32768) % modulus;
}

function solve(n, k) {
  const mod = 1000000007;
  const factorial = new Float64Array(n + 1), inverse = new Float64Array(n + 1);
  factorial[0] = 1;
  for (let i = 1; i <= n; i++) factorial[i] = factorial[i - 1] * i % mod;
  let base = factorial[n], exponent = mod - 2, value = 1;
  while (exponent > 0) {
    if (exponent % 2) value = multiplyMod(value, base);
    base = multiplyMod(base, base); exponent = Math.floor(exponent / 2);
  }
  inverse[n] = value;
  for (let i = n; i > 0; i--) inverse[i - 1] = inverse[i] * i % mod;
  const choose = (a, b) => multiplyMod(multiplyMod(factorial[a], inverse[b]), inverse[a - b]);
  let answer = choose(n - 1, k - 1);
  if ((n - k) % 2 === 0) answer -= choose((n - k) / 2 + k - 1, k - 1);
  return (answer + mod) % mod;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}

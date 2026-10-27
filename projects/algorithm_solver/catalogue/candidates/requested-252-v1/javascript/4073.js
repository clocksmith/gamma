/**
 * 4073. Count Good Strings
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-good-strings/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4073.Count%20Good%20Strings/README_EN.md
 * Complexity: O(log n) modular operations, O(log n) bit-string space.
 * Good strings are exactly strings whose maximal constant-character runs all have odd length. Odd-part compositions of n number F_n; two choices of first character give 2F_n. Fast doubling with exact modular products. n<=10^15 is an exact JS Number.
 */

function multiplyMod(a, b, modulus = 1000000007) {
  const low = a % 32768, high = Math.floor(a / 32768);
  return (low * b + ((high * b) % modulus) * 32768) % modulus;
}

function solve(n) {
  const modulus=1000000007;let a=0,b=1;
  for(const bit of n.toString(2)) {
    const c=multiplyMod(a,(2*b-a+modulus)%modulus,modulus);
    const d=(multiplyMod(a,a,modulus)+multiplyMod(b,b,modulus))%modulus;
    if(bit==='0'){a=c;b=d;}else{a=d;b=(c+d)%modulus;}
  }
  return 2*a%modulus;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}

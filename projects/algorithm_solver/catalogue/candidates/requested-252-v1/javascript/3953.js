/**
 * 3953. Maximum Score with Co-Prime Element
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-score-with-co-prime-element/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3953.Maximum%20Score%20with%20Co-Prime%20Element/README_EN.md
 * Complexity: O(M log M + M*2^omega(M)) time, O(M) space for M <= 100000.
 * Unchanged original values above maxVal remain selectable. Modification limits apply only to replacement values. Coprimality count includes the selected index and explicitly removes its contribution. Inputs preserved; native method pending.
 */

function solve(nums, maxVal) {
  let bound = maxVal;
  for (const value of nums) bound = Math.max(bound, value);
  const frequency = new Int32Array(bound + 1);
  for (const value of nums) frequency[value]++;
  const multiples = new Int32Array(bound + 1);
  const smallestPrime = new Int32Array(bound + 1);
  for (let divisor = 1; divisor <= bound; divisor++) {
    for (let multiple = divisor; multiple <= bound; multiple += divisor) multiples[divisor] += frequency[multiple];
    if (divisor >= 2 && smallestPrime[divisor] === 0) {
      for (let multiple = divisor; multiple <= bound; multiple += divisor) {
        if (smallestPrime[multiple] === 0) smallestPrime[multiple] = divisor;
      }
    }
  }
  let best = 0;
  for (let value = bound; value > best; value--) {
    if (value > maxVal && frequency[value] === 0) continue;
    let cost;
    if (value === 1) cost = frequency[1] ? 0 : 1;
    else {
      const terms = [[1, -1]];
      let remainder = value;
      while (remainder > 1) {
        const prime = smallestPrime[remainder];
        const length = terms.length;
        for (let index = 0; index < length; index++) terms.push([terms[index][0] * prime, -terms[index][1]]);
        while (remainder % prime === 0) remainder /= prime;
      }
      let bad = 0;
      for (let index = 1; index < terms.length; index++) bad += terms[index][1] * multiples[terms[index][0]];
      cost = frequency[value] ? bad - 1 : Math.max(1, bad);
    }
    best = Math.max(best, value - cost);
  }
  return best;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}

/**
 * 3943. Number of Pairs After Increment
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/number-of-pairs-after-increment/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3943.Number%20of%20Pairs%20After%20Increment/README_EN.md
 * Complexity: O(m+q*(sqrt(m)+d*sqrt(m))) time, O(m) space; d<=5.
 * Range additions update internal copy only; later queries see updates. Multiplicities count. Number safe for <=50000 increments of <=1e5. Native name pending.
 */

function solve(nums1, nums2, queries) {
  const values = nums2.slice();
  const width = Math.max(1, Math.floor(Math.sqrt(values.length)));
  const blocks = Math.ceil(values.length / width);
  const lazy = Array(blocks).fill(0);
  const frequency = Array.from({ length: blocks }, () => new Map());
  values.forEach((value, index) => {
    const counts = frequency[Math.floor(index / width)];
    counts.set(value, (counts.get(value) || 0) + 1);
  });
  const firstCounts = new Map();
  for (const value of nums1) firstCounts.set(value, (firstCounts.get(value) || 0) + 1);
  const answer = [];
  for (const query of queries) {
    if (query[0] === 1) {
      const [, left, right, increment] = query;
      for (let block = Math.floor(left / width); block <= Math.floor(right / width); block += 1) {
        const start = block * width;
        const end = Math.min(values.length, start + width);
        if (left <= start && end - 1 <= right) { lazy[block] += increment; continue; }
        const counts = frequency[block];
        for (let index = Math.max(left, start); index < Math.min(right + 1, end); index += 1) {
          const old = values[index];
          if (counts.get(old) === 1) counts.delete(old);
          else counts.set(old, counts.get(old) - 1);
          values[index] += increment;
          counts.set(values[index], (counts.get(values[index]) || 0) + 1);
        }
      }
    } else {
      let pairs = 0;
      for (let block = 0; block < blocks; block += 1) {
        for (const [value, multiplicity] of firstCounts) pairs += multiplicity * (frequency[block].get(query[1] - value - lazy[block]) || 0);
      }
      answer.push(pairs);
    }
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}

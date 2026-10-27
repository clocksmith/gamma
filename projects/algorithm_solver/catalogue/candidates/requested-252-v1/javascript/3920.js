/**
 * 3920. Maximize Fixed Points After Deletions
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximize-fixed-points-after-deletions/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3920.Maximize%20Fixed%20Points%20After%20Deletions/README_EN.md
 * Complexity: O(n log n) time, O(n) space.
 * 0-based fixed points. Nonfixed retained elements may fill gaps. Batches prevent equal-value fixed points. Native name pending.
 */

function solve(nums) {
  const candidates = [];
  for (let index = 0; index < nums.length; index += 1) {
    if (nums[index] <= index) candidates.push([nums[index], index - nums[index]]);
  }
  candidates.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const tree = new Int32Array(nums.length + 2);
  let answer = 0;
  let start = 0;
  while (start < candidates.length) {
    let end = start;
    const pending = [];
    while (end < candidates.length && candidates[end][0] === candidates[start][0]) {
      const position = candidates[end][1] + 1;
      let best = 0;
      for (let cursor = position; cursor > 0; cursor -= cursor & -cursor) best = Math.max(best, tree[cursor]);
      pending.push([position, best + 1]);
      answer = Math.max(answer, best + 1);
      end += 1;
    }
    for (const [position, best] of pending) {
      for (let cursor = position; cursor < tree.length; cursor += cursor & -cursor) tree[cursor] = Math.max(tree[cursor], best);
    }
    start = end;
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}

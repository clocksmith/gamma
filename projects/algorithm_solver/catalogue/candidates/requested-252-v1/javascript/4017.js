/**
 * 4017. Peaks in Array II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/peaks-in-array-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4017.Peaks%20in%20Array%20II/README_EN.md
 * Complexity: O(n + q log n) time, O(n) space.
 * Interior peak-indicator intervals correspond one-to-one to length>=3 subarrays. Count intervals containing 1 via total intervals minus zero runs. Point changes affect at most three peak flags. Caller arrays preserved; native method unconfirmed.
 */

function solve(nums, queries) {
  const values = nums.slice(), n = values.length;
  const empty = [0, 0, 0, 0];
  function merge(a, b) {
    return [a[0] + b[0], a[1] === a[0] ? a[1] + b[1] : a[1], b[2] === b[0] ? b[2] + a[2] : b[2], a[3] + b[3] + a[2] * b[1]];
  }
  function leaf(i) {
    const peak = i > 0 && i < n - 1 && values[i] > values[i - 1] && values[i] > values[i + 1];
    return peak ? [1, 0, 0, 0] : [1, 1, 1, 1];
  }
  let size = 1;
  while (size < n) size *= 2;
  const tree = Array(2 * size).fill(empty);
  for (let i = 0; i < n; i++) tree[size + i] = leaf(i);
  for (let i = size - 1; i > 0; i--) tree[i] = merge(tree[2 * i], tree[2 * i + 1]);
  const answer = [];
  for (const [kind, a, b] of queries) {
    if (kind === 2) {
      values[a] = b;
      for (let index = Math.max(0, a - 1); index < Math.min(n, a + 2); index++) {
        let i = size + index; tree[i] = leaf(index);
        for (i = Math.floor(i / 2); i > 0; i = Math.floor(i / 2)) tree[i] = merge(tree[2 * i], tree[2 * i + 1]);
      }
    } else {
      let left = size + a + 1, right = size + b, before = empty, after = empty;
      while (left < right) {
        if (left % 2) before = merge(before, tree[left++]);
        if (right % 2) after = merge(tree[--right], after);
        left = Math.floor(left / 2); right = Math.floor(right / 2);
      }
      const result = merge(before, after), length = result[0];
      answer.push(length * (length + 1) / 2 - result[3]);
    }
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}

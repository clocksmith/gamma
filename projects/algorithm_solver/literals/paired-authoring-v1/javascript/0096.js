class Solution {
  numTrees(n) {
    const counts = new Array(n + 1).fill(0);
    counts[0] = 1;
    for (let size = 1; size <= n; size += 1) {
      for (let left_size = 0; left_size < size; left_size += 1) {
        const right_size = size - left_size - 1;
        counts[size] += counts[left_size] * counts[right_size];
      }
    }
    return counts[n];
  }
}

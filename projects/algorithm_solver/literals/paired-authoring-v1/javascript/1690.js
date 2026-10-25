class Solution {
  stoneGameVII(stones) {
    const size = stones.length;
    if (size === 0) {
      return 0;
    }
    const prefix = [0];
    for (const value of stones) {
      prefix.push(prefix[prefix.length - 1] + value);
    }
    const scores = Array(size).fill(0);
    for (let length = 2; length <= size; length += 1) {
      for (let left = 0; left <= size - length; left += 1) {
        const right = left + length - 1;
        const removeLeft = prefix[right + 1] - prefix[left + 1] - scores[left + 1];
        const removeRight = prefix[right] - prefix[left] - scores[left];
        scores[left] = Math.max(removeLeft, removeRight);
      }
    }
    return scores[0];
  }
}

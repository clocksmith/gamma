class Solution {
  longestArithSeqLength(nums) {
    if (nums.length < 2) return nums.length;
    const ending = [];
    for (let index = 0; index < nums.length; index += 1) ending.push(new Map());
    let best = 2;
    for (let right = 0; right < nums.length; right += 1) {
      for (let left = 0; left < right; left += 1) {
        const difference = nums[right] - nums[left];
        const length = (ending[left].get(difference) ?? 1) + 1;
        ending[right].set(difference, Math.max(ending[right].get(difference) ?? 0, length));
        best = Math.max(best, ending[right].get(difference));
      }
    }
    return best;
  }
}

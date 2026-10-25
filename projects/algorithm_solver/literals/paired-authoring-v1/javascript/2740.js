class Solution {
  findValueOfPartition(nums) {
    const ordered = nums.slice().sort((first, second) => first - second);
    let best = ordered[1] - ordered[0];
    for (let index = 2; index < ordered.length; index += 1) {
      best = Math.min(best, ordered[index] - ordered[index - 1]);
    }
    return best;
  }
}

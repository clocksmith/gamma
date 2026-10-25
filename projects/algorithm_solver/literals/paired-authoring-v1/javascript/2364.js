class Solution {
  countBadPairs(nums) {
    const frequencies = new Map();
    let bad = 0;
    for (let index = 0; index < nums.length; index += 1) {
      const key = nums[index] - index;
      const good = frequencies.get(key) || 0;
      bad += index - good;
      frequencies.set(key, good + 1);
    }
    return bad;
  }
}

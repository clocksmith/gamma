class Solution {
  arrayChange(nums, operations) {
    const positions = new Map(nums.map((value, index) => [value, index]));
    for (const [previous, replacement] of operations) {
      const index = positions.get(previous);
      positions.delete(previous);
      nums[index] = replacement;
      positions.set(replacement, index);
    }
    return nums;
  }
}

class Solution {
  subarraySum(nums, k) {
    const counts = new Map([[0, 1]]);
    let prefix = 0;
    let result = 0;
    for (const value of nums) {
      prefix += value;
      result += counts.get(prefix - k) ?? 0;
      counts.set(prefix, (counts.get(prefix) ?? 0) + 1);
    }
    return result;
  }
}

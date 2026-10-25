class Solution {
  sumCounts(nums) {
    let answer = 0;
    for (let left = 0; left < nums.length; left += 1) {
      const distinct = new Set();
      for (let right = left; right < nums.length; right += 1) {
        distinct.add(nums[right]);
        const count = distinct.size;
        answer += count * count;
      }
    }
    return answer;
  }
}

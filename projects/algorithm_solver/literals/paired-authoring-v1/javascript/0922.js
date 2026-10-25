class Solution {
  sortArrayByParityII(nums) {
    let odd = 1;
    for (let even = 0; even < nums.length; even += 2) {
      if (nums[even] % 2 !== 0) {
        while (odd < nums.length && nums[odd] % 2 !== 0) {
          odd += 2;
        }
        [nums[even], nums[odd]] = [nums[odd], nums[even]];
      }
    }
    return nums;
  }
}

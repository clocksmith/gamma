class Solution {
  sortArrayByParityII(nums) {
    const result = new Array(nums.length).fill(0);
    let even = 0;
    let odd = 1;
    for (const value of nums) {
      if (value % 2 === 0) {
        result[even] = value;
        even += 2;
      } else {
        result[odd] = value;
        odd += 2;
      }
    }
    return result;
  }
}

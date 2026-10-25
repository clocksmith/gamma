class Solution {
  getSumAbsoluteDifferences(nums) {
    let total = 0;
    for (const value of nums) {
      total += value;
    }
    let leftSum = 0;
    const output = [];
    for (let index = 0; index < nums.length; index += 1) {
      const value = nums[index];
      const left = value * index - leftSum;
      const right = total - leftSum - value - value * (nums.length - index - 1);
      output.push(left + right);
      leftSum += value;
    }
    return output;
  }
}

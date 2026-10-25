class Solution {
  maximumTripletValue(nums) {
    let largest = nums[0];
    let difference = 0;
    let answer = 0;
    for (let index = 1; index < nums.length; index += 1) {
      const value = nums[index];
      answer = Math.max(answer, difference * value);
      difference = Math.max(difference, largest - value);
      largest = Math.max(largest, value);
    }
    return answer;
  }
}

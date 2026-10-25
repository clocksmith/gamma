class Solution {
  sortedSquares(nums) {
    const result = new Array(nums.length).fill(0);
    let left = 0;
    let right = nums.length - 1;
    for (let write = nums.length - 1; write >= 0; write -= 1) {
      const left_square = nums[left] * nums[left];
      const right_square = nums[right] * nums[right];
      if (left_square > right_square) {
        result[write] = left_square;
        left += 1;
      } else {
        result[write] = right_square;
        right -= 1;
      }
    }
    return result;
  }
}

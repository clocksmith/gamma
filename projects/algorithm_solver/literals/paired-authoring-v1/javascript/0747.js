class Solution {
  dominantIndex(nums) {
    if (nums.length === 0) {
      return -1;
    }

    let largest = 0;
    for (let index = 1; index < nums.length; index += 1) {
      if (nums[index] > nums[largest]) {
        largest = index;
      }
    }
    for (let index = 0; index < nums.length; index += 1) {
      if (index !== largest && 2 * nums[index] > nums[largest]) {
        return -1;
      }
    }
    return largest;
  }
}

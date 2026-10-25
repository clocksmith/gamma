class Solution {
  findKDistantIndices(nums, key, k) {
    const output = [];
    let nextIndex = 0;
    for (let index = 0; index < nums.length; index += 1) {
      if (nums[index] === key) {
        const left = Math.max(nextIndex, index - k);
        const right = Math.min(nums.length - 1, index + k);
        for (let position = left; position <= right; position += 1) {
          output.push(position);
        }
        nextIndex = right + 1;
      }
    }
    return output;
  }
}

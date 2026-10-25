class Solution {
  minimumSeconds(nums) {
    const positions = new Map();
    for (let index = 0; index < nums.length; index += 1) {
      const value = nums[index];
      if (!positions.has(value)) {
        positions.set(value, []);
      }
      positions.get(value).push(index);
    }
    let answer = nums.length;
    for (const indices of positions.values()) {
      let gap = indices[0] + nums.length - indices[indices.length - 1];
      for (let index = 1; index < indices.length; index += 1) {
        gap = Math.max(gap, indices[index] - indices[index - 1]);
      }
      answer = Math.min(answer, Math.floor(gap / 2));
    }
    return answer;
  }
}

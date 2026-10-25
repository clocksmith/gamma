class Solution {
  minIncrementForUnique(nums) {
    const ordered = nums.slice().sort((left, right) => {
      if (left < right) {
        return -1;
      }
      if (left > right) {
        return 1;
      }
      return 0;
    });
    let next_free = 0;
    let moves = 0;
    for (const value of ordered) {
      const assigned = Math.max(value, next_free);
      moves += assigned - value;
      next_free = assigned + 1;
    }
    return moves;
  }
}

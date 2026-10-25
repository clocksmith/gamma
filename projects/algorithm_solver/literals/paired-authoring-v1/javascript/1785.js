class Solution {
  minElements(nums, limit, goal) {
    let total = 0;
    for (const value of nums) {
      total += value;
    }
    const gap = Math.abs(goal - total);
    const remainder = gap % limit;
    const quotient = (gap - remainder) / limit;
    return quotient + (remainder === 0 ? 0 : 1);
  }
}

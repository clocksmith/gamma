function floorSqrt(value) {
  let lower = 0;
  // Largest root whose square is a safe integer in both languages.
  let upper = Math.min(value, 94906265) + 1;
  while (lower < upper) {
    const middle = lower + Math.floor((upper - lower) / 2);
    if (middle * middle <= value) {
      lower = middle + 1;
    } else {
      upper = middle;
    }
  }
  return lower - 1;
}

class Solution {
  judgeSquareSum(c) {
    let left = 0;
    let right = floorSqrt(c);
    while (left <= right) {
      const total = left * left + right * right;
      if (total === c) {
        return true;
      }
      if (total < c) {
        left += 1;
      } else {
        right -= 1;
      }
    }
    return false;
  }
}

class Solution {
  mySqrt(x) {
    let lower = 0;
    // Largest root whose square is a safe integer in both languages.
    let upper = Math.min(x, 94906265) + 1;
    while (lower < upper) {
      const middle = lower + Math.floor((upper - lower) / 2);
      if (middle * middle <= x) {
        lower = middle + 1;
      } else {
        upper = middle;
      }
    }
    return lower - 1;
  }
}

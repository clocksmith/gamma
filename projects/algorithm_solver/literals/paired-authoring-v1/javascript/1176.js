class Solution {
  dietPlanPerformance(calories, k, lower, upper) {
    let window = 0;
    let score = 0;
    for (let right = 0; right < calories.length; right += 1) {
      window += calories[right];
      if (right >= k) {
        window -= calories[right - k];
      }
      if (right + 1 >= k) {
        if (window < lower) {
          score -= 1;
        } else if (window > upper) {
          score += 1;
        }
      }
    }
    return score;
  }
}

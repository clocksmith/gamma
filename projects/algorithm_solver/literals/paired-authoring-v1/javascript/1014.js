class Solution {
  maxScoreSightseeingPair(values) {
    let bestLeft = values[0];
    let best = values[0] + values[1] - 1;
    for (let right = 1; right < values.length; right += 1) {
      best = Math.max(best, bestLeft + values[right] - right);
      bestLeft = Math.max(bestLeft, values[right] + right);
    }
    return best;
  }
}

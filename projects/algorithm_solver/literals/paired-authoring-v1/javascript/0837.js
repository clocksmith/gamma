class Solution {
  new21Game(n, k, maxPts) {
    if (k === 0 || n >= k - 1 + maxPts) {
      return 1;
    }

    const probabilities = new Array(n + 1).fill(0);
    probabilities[0] = 1;
    let window = 1;
    let answer = 0;
    for (let score = 1; score <= n; score += 1) {
      probabilities[score] = window / maxPts;
      if (score < k) {
        window += probabilities[score];
      } else {
        answer += probabilities[score];
      }
      const outgoing = score - maxPts;
      if (outgoing >= 0 && outgoing < k) {
        window -= probabilities[outgoing];
      }
    }
    return Math.min(1, Math.max(0, answer));
  }
}

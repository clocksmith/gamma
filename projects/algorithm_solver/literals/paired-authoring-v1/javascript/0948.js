class Solution {
  bagOfTokensScore(tokens, power) {
    const ordered = tokens.slice().sort((left, right) => left - right);
    let left = 0;
    let right = ordered.length - 1;
    let score = 0;
    let best = 0;
    while (left <= right) {
      if (ordered[left] <= power) {
        power -= ordered[left];
        left += 1;
        score += 1;
        best = Math.max(best, score);
      } else if (score > 0 && left < right) {
        power += ordered[right];
        right -= 1;
        score -= 1;
      } else {
        break;
      }
    }
    return best;
  }
}

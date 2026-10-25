class Solution {
  numPairsDivisibleBy60(time) {
    const counts = new Array(60).fill(0);
    let pairs = 0;
    for (const duration of time) {
      const remainder = duration % 60;
      pairs += counts[(60 - remainder) % 60];
      counts[remainder] += 1;
    }
    return pairs;
  }
}

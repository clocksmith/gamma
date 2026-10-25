class Solution {
  nonSpecialCount(l, r) {
    let left = 0;
    let right = 31623;
    while (left < right) {
      const middle = left + Math.floor((right - left + 1) / 2);
      if (middle * middle <= r) {
        left = middle;
      } else {
        right = middle - 1;
      }
    }
    const limit = left;
    const prime = Array(limit + 1).fill(true);
    prime[0] = false;
    if (limit >= 1) {
      prime[1] = false;
    }
    let candidate = 2;
    while (candidate * candidate <= limit) {
      if (prime[candidate]) {
        for (let multiple = candidate * candidate; multiple <= limit; multiple += candidate) {
          prime[multiple] = false;
        }
      }
      candidate += 1;
    }
    let special = 0;
    for (let value = 2; value <= limit; value += 1) {
      if (prime[value] && value * value >= l) {
        special += 1;
      }
    }
    return r - l + 1 - special;
  }
}

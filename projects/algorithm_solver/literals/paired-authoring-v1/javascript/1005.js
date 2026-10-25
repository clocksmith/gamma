class Solution {
  largestSumAfterKNegations(nums, k) {
    const ordered = nums.slice().sort((left, right) => left - right);
    for (let index = 0; index < ordered.length; index += 1) {
      if (k === 0 || ordered[index] >= 0) break;
      ordered[index] = -ordered[index];
      k -= 1;
    }
    let total = 0;
    let smallest = Math.abs(ordered[0]);
    for (const value of ordered) {
      total += value;
      smallest = Math.min(smallest, Math.abs(value));
    }
    if (k % 2 === 1) total -= 2 * smallest;
    return total;
  }
}

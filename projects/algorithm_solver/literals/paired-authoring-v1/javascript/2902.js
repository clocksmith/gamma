class Solution {
  countSubMultisets(nums, l, r) {
    const frequencies = new Map();
    for (const value of nums) {
      frequencies.set(value, (frequencies.get(value) || 0) + 1);
    }
    const modulus = 1000000007;
    let counts = Array(r + 1).fill(0);
    counts[0] = (frequencies.get(0) || 0) + 1;
    for (const [value, multiplicity] of frequencies) {
      if (value === 0 || value > r) {
        continue;
      }
      const following = Array(r + 1).fill(0);
      const excluded = (multiplicity + 1) * value;
      for (let total = 0; total <= r; total += 1) {
        let ways = counts[total];
        if (total >= value) {
          ways += following[total - value];
        }
        if (total >= excluded) {
          ways -= counts[total - excluded];
        }
        following[total] = (ways + modulus) % modulus;
      }
      counts = following;
    }
    let answer = 0;
    for (let total = l; total <= r; total += 1) {
      answer = (answer + counts[total]) % modulus;
    }
    return answer;
  }
}

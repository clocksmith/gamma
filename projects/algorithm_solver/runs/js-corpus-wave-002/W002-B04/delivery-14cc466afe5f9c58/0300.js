function lengthOfLIS(nums) {
  const tails = [];
  for (const value of nums) {
    let left = 0, right = tails.length;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (tails[middle] < value) left = middle + 1;
      else right = middle;
    }
    tails[left] = value;
  }
  return tails.length;
}

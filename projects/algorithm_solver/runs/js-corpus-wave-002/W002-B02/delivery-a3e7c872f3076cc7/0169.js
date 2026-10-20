function majorityElement(nums) {
  let candidate = 0;
  let balance = 0;

  for (const value of nums) {
    if (balance === 0) {
      candidate = value;
    }
    balance += value === candidate ? 1 : -1;
  }

  return candidate;
}

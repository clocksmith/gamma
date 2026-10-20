function singleNumber(nums) {
  let seenOnce = 0;
  let seenTwice = 0;

  for (const value of nums) {
    seenOnce = (seenOnce ^ value) & ~seenTwice;
    seenTwice = (seenTwice ^ value) & ~seenOnce;
  }

  return seenOnce;
}

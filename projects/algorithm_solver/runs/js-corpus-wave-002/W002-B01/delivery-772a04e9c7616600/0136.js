function singleNumber(nums) {
  let unique = 0;

  for (const value of nums) {
    unique ^= value;
  }

  return unique;
}

function singleNumber(nums) {
  let xor = 0;
  for (const value of nums) xor ^= value;
  const bit = xor & -xor;
  let first = 0, second = 0;
  for (const value of nums) {
    if (value & bit) first ^= value;
    else second ^= value;
  }
  return [first, second];
}

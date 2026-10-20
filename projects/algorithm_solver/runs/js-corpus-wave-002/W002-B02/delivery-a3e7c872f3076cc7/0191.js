function hammingWeight(n) {
  let value = n >>> 0;
  let count = 0;

  while (value !== 0) {
    value = (value & (value - 1)) >>> 0;
    count += 1;
  }

  return count;
}

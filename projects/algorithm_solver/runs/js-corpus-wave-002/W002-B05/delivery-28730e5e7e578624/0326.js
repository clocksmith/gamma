function isPowerOfThree(n) {
  return Number.isInteger(n) && n > 0 && 1162261467 % n === 0;
}

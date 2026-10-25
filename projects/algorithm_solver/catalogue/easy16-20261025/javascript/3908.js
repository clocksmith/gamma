function solve(n, x) {
  // O(d) time and auxiliary space for the decimal representation.
  const digits = String(n);
  const digit = String(x);
  return digits[0] !== digit && digits.includes(digit);
}

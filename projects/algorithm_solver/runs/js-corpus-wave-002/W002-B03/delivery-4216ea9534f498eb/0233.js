function countDigitOne(n) {
  let result = 0;
  for (let factor = 1; factor <= n; factor *= 10) {
    const high = Math.floor(n / (factor * 10));
    const digit = Math.floor(n / factor) % 10;
    result += high * factor + (digit === 1 ? n % factor + 1 : digit > 1 ? factor : 0);
  }
  return result;
}

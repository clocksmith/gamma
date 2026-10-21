function solve(values) {
  if (typeof values === 'number' && !Number.isSafeInteger(values))
    throw new RangeError('Exact integer required');
  let value = BigInt(values);
  if (value < 0n || value !== 0n && value % 10n === 0n)
    return false;
  let value2 = 0n;
  while (value > value2) {
    value2 = value2 * 10n + value % 10n;
    value /= 10n;
  }
  return value === value2 || value === value2 / 10n;
}

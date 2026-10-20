function isPalindrome(x) {
  if (typeof x === 'number' && !Number.isSafeInteger(x)) throw new RangeError('Exact integer required');
  let remaining = BigInt(x);
  if (remaining < 0n || (remaining !== 0n && remaining % 10n === 0n)) return false;
  let reversedHalf = 0n;
  while (remaining > reversedHalf) {
    reversedHalf = reversedHalf * 10n + remaining % 10n;
    remaining /= 10n;
  }
  return remaining === reversedHalf || remaining === reversedHalf / 10n;
}

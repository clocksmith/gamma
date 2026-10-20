function reverse(x) {
  const sign = x < 0 ? -1 : 1;
  const magnitudeLimit = sign < 0 ? 2147483648 : 2147483647;
  let remaining = Math.abs(x);
  let reversedValue = 0;
  while (remaining > 0) {
    const digit = remaining % 10;

    // Check before multiplying, rather than overflowing and truncating.
    if (reversedValue > Math.floor((magnitudeLimit - digit) / 10)) {
      return 0;
    }
    reversedValue = reversedValue * 10 + digit;
    remaining = Math.trunc(remaining / 10);
  }
  return sign * reversedValue;
}

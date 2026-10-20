function isHappy(n) {
  function nextValue(value) {
    let remaining = value;
    let total = 0;

    while (remaining > 0) {
      const digit = remaining % 10;
      total += digit * digit;
      remaining = Math.floor(remaining / 10);
    }

    return total;
  }

  const seen = new Set();
  let current = n;

  while (current !== 1 && !seen.has(current)) {
    seen.add(current);
    current = nextValue(current);
  }

  return current === 1;
}

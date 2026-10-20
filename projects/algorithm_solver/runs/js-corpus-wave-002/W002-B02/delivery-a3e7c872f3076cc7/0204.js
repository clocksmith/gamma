function countPrimes(n) {
  if (n <= 2) {
    return 0;
  }

  const composite = new Uint8Array(n);
  let count = 0;

  for (let value = 2; value < n; value += 1) {
    if (composite[value] !== 0) {
      continue;
    }

    count += 1;
    if (value * value >= n) {
      continue;
    }

    for (
      let multiple = value * value;
      multiple < n;
      multiple += value
    ) {
      composite[multiple] = 1;
    }
  }

  return count;
}

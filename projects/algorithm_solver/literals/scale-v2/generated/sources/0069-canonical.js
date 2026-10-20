function solve(values) {
  const value = BigInt(values);
  let index = 0n;
  let index2 = value;
  let value2 = 0n;
  while (index <= index2) {
    const value3 = index + (index2 - index) / 2n;
    if (value3 === 0n || value3 <= value / value3) {
      value2 = value3;
      index = value3 + 1n;
    } else {
      index2 = value3 - 1n;
    }
  }
  return value2 <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(value2) : value2;
}

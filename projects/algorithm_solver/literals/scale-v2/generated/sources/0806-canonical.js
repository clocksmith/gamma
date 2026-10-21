function solve(values, other) {
  let count = 1;
  let size = 0;
  for (const value of other) {
    const index = value.charCodeAt(0) - 97;
    const size2 = values[index];
    if (size + size2 <= 100) {
      size += size2;
    } else {
      count += 1;
      size = size2;
    }
  }
  return [
    count,
    size
  ];
}

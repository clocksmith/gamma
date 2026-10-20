function lexicalOrder(n) {
  const result = [];
  let current = 1;
  for (let count = 0; count < n; count++) {
    result.push(current);
    if (current * 10 <= n) {
      current *= 10;
    } else {
      while (current % 10 === 9 || current + 1 > n) {
        current = Math.floor(current / 10);
      }
      current++;
    }
  }
  return result;
}

function nthUglyNumber(n) {
  const ugly = [1];
  let i2 = 0, i3 = 0, i5 = 0;
  while (ugly.length < n) {
    const next = Math.min(ugly[i2] * 2, ugly[i3] * 3, ugly[i5] * 5);
    ugly.push(next);
    if (ugly[i2] * 2 === next) i2++;
    if (ugly[i3] * 3 === next) i3++;
    if (ugly[i5] * 5 === next) i5++;
  }
  return ugly[n - 1];
}

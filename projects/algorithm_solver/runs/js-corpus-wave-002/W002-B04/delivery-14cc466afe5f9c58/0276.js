function numWays(n, k) {
  if (n === 0 || k === 0) return 0;
  if (n === 1) return k;
  let same = k, different = k * (k - 1);
  for (let post = 3; post <= n; post++) {
    [same, different] = [different, (same + different) * (k - 1)];
  }
  return same + different;
}

function minCut(s) {
  const length = s.length;
  if (length === 0) {
    return 0;
  }

  const palindrome = Array.from(
    { length },
    () => new Array(length).fill(false)
  );
  const cuts = new Array(length).fill(0);

  for (let end = 0; end < length; end += 1) {
    cuts[end] = end;
    for (let start = 0; start <= end; start += 1) {
      if (
        s[start] === s[end] &&
        (end - start <= 2 || palindrome[start + 1][end - 1])
      ) {
        palindrome[start][end] = true;
        cuts[end] = start === 0
          ? 0
          : Math.min(cuts[end], cuts[start - 1] + 1);
      }
    }
  }

  return cuts[length - 1];
}

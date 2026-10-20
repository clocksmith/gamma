function shortestPalindrome(s) {
  const reversed = [...s].reverse().join('');
  const combined = `${s}#${reversed}`;
  const prefix = new Array(combined.length).fill(0);

  for (let index = 1; index < combined.length; index += 1) {
    let matched = prefix[index - 1];

    while (
      matched > 0 &&
      combined[index] !== combined[matched]
    ) {
      matched = prefix[matched - 1];
    }

    if (combined[index] === combined[matched]) {
      matched += 1;
    }

    prefix[index] = matched;
  }

  const palindromePrefixLength = prefix[combined.length - 1] ?? 0;
  return reversed.slice(0, s.length - palindromePrefixLength) + s;
}

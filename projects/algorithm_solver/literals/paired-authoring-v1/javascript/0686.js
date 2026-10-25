function prefixLengths(pattern) {
  const prefix = new Array(pattern.length).fill(0);
  let matched = 0;
  for (let index = 1; index < pattern.length; index += 1) {
    while (matched > 0 && pattern[index] !== pattern[matched]) {
      matched = prefix[matched - 1];
    }
    if (pattern[index] === pattern[matched]) {
      matched += 1;
    }
    prefix[index] = matched;
  }
  return prefix;
}

class Solution {
  repeatedStringMatch(a, b) {
    if (b.length === 0) {
      return 0;
    }

    const prefix = prefixLengths(b);
    let matched = 0;
    for (let index = 0; index < a.length + b.length - 1; index += 1) {
      const character = a[index % a.length];
      while (matched > 0 && character !== b[matched]) {
        matched = prefix[matched - 1];
      }
      if (character === b[matched]) {
        matched += 1;
      }
      if (matched === b.length) {
        return Math.floor(index / a.length) + 1;
      }
    }
    return -1;
  }
}

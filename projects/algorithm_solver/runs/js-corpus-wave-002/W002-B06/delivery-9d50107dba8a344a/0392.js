function isSubsequence(s, t) {
  let matched = 0;
  for (let index = 0; index < t.length && matched < s.length; index++) {
    if (s[matched] === t[index]) matched++;
  }
  return matched === s.length;
}

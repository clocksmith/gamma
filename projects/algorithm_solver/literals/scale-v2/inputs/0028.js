/* 28. Find the Index of the First Occurrence in a String */
function strStr(haystack, needle) {
  if (needle.length === 0) {
    return 0;
  }
  const pi = new Array(needle.length).fill(0);
  for (let index = 1, prefixLength = 0; index < needle.length; index++) {
    while (prefixLength > 0 && needle[index] !== needle[prefixLength]) {
      prefixLength = pi[prefixLength - 1];
    }
    if (needle[index] === needle[prefixLength]) {
      prefixLength++;
    }
    pi[index] = prefixLength;
  }
  for (let index = 0, prefixLength = 0; index < haystack.length; index++) {
    while (prefixLength > 0 && haystack[index] !== needle[prefixLength]) {
      prefixLength = pi[prefixLength - 1];
    }
    if (haystack[index] === needle[prefixLength]) {
      prefixLength++;
    }
    if (prefixLength === needle.length) {
      return index - prefixLength + 1;
    }
  }
  return -1;
}

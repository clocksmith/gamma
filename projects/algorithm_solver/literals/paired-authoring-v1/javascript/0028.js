class Solution {
  strStr(haystack, needle) {
    if (needle.length === 0) {
      return 0;
    }

    const prefix = new Array(needle.length).fill(0);
    let matched = 0;
    for (let index = 1; index < needle.length; index += 1) {
      while (matched > 0 && needle[index] !== needle[matched]) {
        matched = prefix[matched - 1];
      }
      if (needle[index] === needle[matched]) {
        matched += 1;
      }
      prefix[index] = matched;
    }

    matched = 0;
    for (let index = 0; index < haystack.length; index += 1) {
      const character = haystack[index];
      while (matched > 0 && character !== needle[matched]) {
        matched = prefix[matched - 1];
      }
      if (character === needle[matched]) {
        matched += 1;
      }
      if (matched === needle.length) {
        return index - needle.length + 1;
      }
    }
    return -1;
  }
}

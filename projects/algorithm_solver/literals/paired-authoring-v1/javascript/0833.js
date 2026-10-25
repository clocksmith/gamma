class Solution {
  findReplaceString(s, indices, sources, targets) {
    const matches = new Map();
    for (let operation = 0; operation < indices.length; operation += 1) {
      const index = indices[operation];
      if (s.startsWith(sources[operation], index)) {
        matches.set(index, operation);
      }
    }
    const result = [];
    let index = 0;
    while (index < s.length) {
      if (matches.has(index)) {
        const operation = matches.get(index);
        result.push(targets[operation]);
        index += sources[operation].length;
      } else {
        result.push(s[index]);
        index += 1;
      }
    }
    return result.join("");
  }
}

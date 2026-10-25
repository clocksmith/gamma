class Solution {
  canConvert(source, target) {
    if (source === target) {
      return true;
    }
    const mapping = new Map();
    for (let index = 0; index < source.length; index += 1) {
      const character = source[index];
      const replacement = target[index];
      if (mapping.has(character) && mapping.get(character) !== replacement) {
        return false;
      }
      mapping.set(character, replacement);
    }
    return new Set(target).size < 26;
  }
}

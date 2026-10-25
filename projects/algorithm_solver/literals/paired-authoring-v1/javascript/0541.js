class Solution {
  reverseStr(s, k) {
    const characters = s.split("");
    for (let start = 0; start < characters.length; start += 2 * k) {
      let left = start;
      let right = Math.min(start + k, characters.length) - 1;
      while (left < right) {
        const saved = characters[left];
        characters[left] = characters[right];
        characters[right] = saved;
        left += 1;
        right -= 1;
      }
    }
    return characters.join("");
  }
}

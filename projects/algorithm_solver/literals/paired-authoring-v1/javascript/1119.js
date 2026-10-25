class Solution {
  removeVowels(text) {
    const kept = [];
    for (const character of text) {
      if (!"aeiou".includes(character)) {
        kept.push(character);
      }
    }
    return kept.join("");
  }
}

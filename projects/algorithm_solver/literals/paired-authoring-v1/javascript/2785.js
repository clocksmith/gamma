class Solution {
  sortVowels(s) {
    const vowelSet = new Set("AEIOUaeiou");
    const vowels = Array.from(s).filter(character => vowelSet.has(character)).sort();
    const output = Array.from(s);
    let nextVowel = 0;
    for (let index = 0; index < output.length; index += 1) {
      if (vowelSet.has(output[index])) {
        output[index] = vowels[nextVowel];
        nextVowel += 1;
      }
    }
    return output.join("");
  }
}

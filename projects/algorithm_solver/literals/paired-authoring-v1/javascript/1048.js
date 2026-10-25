class Solution {
  longestStrChain(words) {
    const ordered = words.slice().sort((left, right) => left.length - right.length);
    const ending = new Map();
    let best = 0;
    for (const word of ordered) {
      let length = 1;
      for (let index = 0; index < word.length; index += 1) {
        const predecessor = word.slice(0, index) + word.slice(index + 1);
        length = Math.max(length, (ending.get(predecessor) ?? 0) + 1);
      }
      ending.set(word, Math.max(ending.get(word) ?? 0, length));
      best = Math.max(best, ending.get(word));
    }
    return best;
  }
}

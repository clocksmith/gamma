class Solution {
  ladderLength(beginWord, endWord, wordList) {
    const remaining = new Set(wordList);
    if (!remaining.has(endWord)) {
      return 0;
    }
    remaining.delete(beginWord);
    const queue = [[beginWord, 1]];
    let head = 0;
    const alphabet = "abcdefghijklmnopqrstuvwxyz";
    while (head < queue.length) {
      const [word, distance] = queue[head];
      head += 1;
      if (word === endWord) {
        return distance;
      }
      for (let position = 0; position < word.length; position += 1) {
        for (const letter of alphabet) {
          if (letter === word[position]) {
            continue;
          }
          const candidate = word.slice(0, position) + letter + word.slice(position + 1);
          if (remaining.has(candidate)) {
            remaining.delete(candidate);
            queue.push([candidate, distance + 1]);
          }
        }
      }
    }
    return 0;
  }
}

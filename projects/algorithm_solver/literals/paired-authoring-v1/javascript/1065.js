class Solution {
  indexPairs(text, words) {
    const children = [new Map()];
    const terminal = [false];
    for (const word of words) {
      let node = 0;
      for (const character of word) {
        if (!children[node].has(character)) {
          children[node].set(character, children.length);
          children.push(new Map());
          terminal.push(false);
        }
        node = children[node].get(character);
      }
      terminal[node] = true;
    }
    const pairs = [];
    for (let start = 0; start < text.length; start += 1) {
      let node = 0;
      for (let end = start; end < text.length; end += 1) {
        const character = text[end];
        if (!children[node].has(character)) {
          break;
        }
        node = children[node].get(character);
        if (terminal[node]) {
          pairs.push([start, end]);
        }
      }
    }
    return pairs;
  }
}

class Solution {
  generateSentences(synonyms, text) {
    const graph = new Map();
    for (const [left, right] of synonyms) {
      if (!graph.has(left)) {
        graph.set(left, new Set());
      }
      if (!graph.has(right)) {
        graph.set(right, new Set());
      }
      graph.get(left).add(right);
      graph.get(right).add(left);
    }
    const groups = new Map();
    for (const root of graph.keys()) {
      if (groups.has(root)) {
        continue;
      }
      const pending = [root];
      const seen = new Set([root]);
      const component = [];
      while (pending.length > 0) {
        const word = pending.pop();
        component.push(word);
        for (const neighbor of graph.get(word)) {
          if (!seen.has(neighbor)) {
            seen.add(neighbor);
            pending.push(neighbor);
          }
        }
      }
      component.sort();
      for (const word of component) {
        groups.set(word, component);
      }
    }
    let sentences = [""];
    for (const word of text.split(" ")) {
      const expanded = [];
      for (const prefix of sentences) {
        for (const replacement of (groups.get(word) || [word])) {
          expanded.push(prefix + (prefix ? " " : "") + replacement);
        }
      }
      sentences = expanded;
    }
    return sentences.sort();
  }
}

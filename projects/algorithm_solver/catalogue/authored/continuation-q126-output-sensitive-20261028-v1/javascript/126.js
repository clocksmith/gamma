'use strict';

var findLadders = function(beginWord, endWord, wordList) {
    const words = [beginWord];
    const indexByWord = new Map([[beginWord, 0]]);
    for (const word of wordList) {
        if (!indexByWord.has(word)) {
            indexByWord.set(word, words.length);
            words.push(word);
        }
    }
    const target = indexByWord.get(endWord);
    if (target === undefined) return [];

    const distance = new Array(words.length).fill(-1);
    distance[0] = 0;
    const parents = Array.from({length: words.length}, () => []);
    const queue = [0];
    let head = 0;
    let targetDepth = -1;
    const alphabet = 'abcdefghijklmnopqrstuvwxyz';
    const length = beginWord.length;
    while (head < queue.length) {
        const node = queue[head++];
        if (targetDepth !== -1 && distance[node] >= targetDepth) break;
        const word = words[node];
        const nextDepth = distance[node] + 1;
        for (let position = 0; position < length; position++) {
            const prefix = word.slice(0, position);
            const suffix = word.slice(position + 1);
            for (const letter of alphabet) {
                if (letter === word[position]) continue;
                const neighbor = indexByWord.get(prefix + letter + suffix);
                if (neighbor === undefined) continue;
                if (distance[neighbor] === -1) {
                    distance[neighbor] = nextDepth;
                    queue.push(neighbor);
                }
                if (distance[neighbor] === nextDepth) {
                    parents[neighbor].push(node);
                    if (neighbor === target) targetDepth = nextDepth;
                }
            }
        }
    }
    if (targetDepth === -1) return [];

    const answers = [];
    const reversePath = [target];
    const parentCursor = [0];
    while (reversePath.length) {
        const node = reversePath[reversePath.length - 1];
        if (node === 0) {
            const answer = new Array(reversePath.length);
            for (let i = 0; i < reversePath.length; i++) {
                answer[i] = words[reversePath[reversePath.length - 1 - i]];
            }
            answers.push(answer);
            reversePath.pop();
            parentCursor.pop();
            continue;
        }
        const last = parentCursor.length - 1;
        const offset = parentCursor[last];
        if (offset === parents[node].length) {
            reversePath.pop();
            parentCursor.pop();
            continue;
        }
        parentCursor[last] = offset + 1;
        reversePath.push(parents[node][offset]);
        parentCursor.push(0);
    }
    return answers;
};

module.exports = {findLadders};

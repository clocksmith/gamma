'use strict';

var wordBreak = function(s, wordDict) {
    const children = [new Array(26).fill(-1)];
    const terminal = [null];
    let maximumWordLength = 0;
    for (const word of wordDict) {
        maximumWordLength = Math.max(maximumWordLength, word.length);
        let node = 0;
        for (let position = 0; position < word.length; position++) {
            const letter = word.charCodeAt(position) - 97;
            let following = children[node][letter];
            if (following === -1) {
                following = children.length;
                children[node][letter] = following;
                children.push(new Array(26).fill(-1));
                terminal.push(null);
            }
            node = following;
        }
        terminal[node] = word;
    }

    const length = s.length;
    const edges = Array.from({length}, () => []);
    for (let start = 0; start < length; start++) {
        let node = 0;
        const limit = Math.min(length, start + maximumWordLength);
        for (let end = start; end < limit; end++) {
            node = children[node][s.charCodeAt(end) - 97];
            if (node === -1) break;
            const word = terminal[node];
            if (word !== null) edges[start].push([end + 1, word]);
        }
    }

    const canFinish = new Array(length + 1).fill(false);
    canFinish[length] = true;
    for (let start = length - 1; start >= 0; start--) {
        canFinish[start] = edges[start].some(edge => canFinish[edge[0]]);
    }
    if (!canFinish[0]) return [];
    for (let start = 0; start < length; start++) {
        edges[start] = edges[start].filter(edge => canFinish[edge[0]]);
    }

    const answers = [];
    const path = [];
    function emit(start) {
        if (start === length) {
            answers.push(path.join(' '));
            return;
        }
        for (const [end, word] of edges[start]) {
            path.push(word);
            emit(end);
            path.pop();
        }
    }
    emit(0);
    return answers;
};

module.exports = {wordBreak};

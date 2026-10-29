// 524 — Longest Word in Dictionary through Deleting. Original implementation; authored candidate, not independently qualified.
function solve(s,dictionary) {
  let answer='';for(const word of dictionary){if(word.length<answer.length||(word.length===answer.length&&word>=answer))continue;let i=0;for(const char of s)if(i<word.length&&word[i]===char)i++;if(i===word.length)answer=word;}return answer;
}

module.exports = { solve, findLongestWord: solve };
